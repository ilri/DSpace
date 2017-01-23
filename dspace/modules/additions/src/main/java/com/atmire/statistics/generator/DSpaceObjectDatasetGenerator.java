package com.atmire.statistics.generator;

import com.atmire.statistics.content.DatasetQuery;
import com.atmire.statistics.content.filter.FilterWithLabel;
import com.atmire.statistics.content.filter.StatisticsDsoFilter;
import com.atmire.statistics.params.SolrLoggerParams;
import com.atmire.statistics.util.SolrResultAttributesResolver;
import org.apache.commons.collections.CollectionUtils;
import org.apache.commons.lang.*;
import org.apache.commons.lang3.ArrayUtils;
import org.apache.solr.client.solrj.SolrServerException;
import org.apache.solr.client.solrj.response.QueryResponse;
import org.apache.solr.client.solrj.util.ClientUtils;
import org.apache.solr.common.SolrDocumentList;
import org.apache.xpath.XPathAPI;
import org.dspace.content.DSpaceObject;
import org.dspace.core.ConfigurationManager;
import org.dspace.core.Constants;
import org.dspace.core.Context;
import org.dspace.statistics.Dataset;
import org.dspace.statistics.ObjectCount;
import org.dspace.statistics.SolrLogger;
import org.dspace.statistics.content.DatasetGenerator;
import org.dspace.statistics.content.DatasetTimeGenerator;
import org.dspace.statistics.content.StatisticsData;
import org.dspace.statistics.content.filter.StatisticsFilter;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

import javax.xml.transform.TransformerException;
import java.sql.SQLException;
import java.text.ParseException;
import java.util.*;

/**
 * Created by Art Lowel (art at atmire dot com)
 * Date: 27-jan-2010
 * Time: 14:17:12
 */
public class DSpaceObjectDatasetGenerator extends DatasetGenerator {

//    public static final Message T_REPOSITORY_ALL = new Message("default", "xmlui.reporting-suite.statistics.graph-editor.data-source.type.repository.all");
//    public static final Message T_COMMUNITIES_ALL = new Message("default", "xmlui.reporting-suite.statistics.graph-editor.data-source.type.communities.all");
//    public static final Message T_COLLECTIONS_ALL = new Message("default", "xmlui.reporting-suite.statistics.graph-editor.data-source.type.collections.all");
//    public static final Message T_ITEMS_ALL = new Message("default", "xmlui.reporting-suite.statistics.graph-editor.data-source.type.items.all");
//    public static final Message T_BITSTREAMS_ALL = new Message("default", "xmlui.reporting-suite.statistics.graph-editor.data-source.type.bitstreams.all");

    protected int type;

    protected boolean percentOfTotal = false;
    protected boolean splitByYear = false;

    /**
     * The number of values shown (max) *
     */
    protected int max;
    protected boolean useFacetTerms = false;
    private boolean showLinks;
    private String columnLabel;

    public boolean isUseFacetTerms() {
        return useFacetTerms;
    }

    public void setUseFacetTerms(boolean useFacetTerms) {
        this.useFacetTerms = useFacetTerms;
    }

    public DSpaceObjectDatasetGenerator(int type) {
        this.type = type;
    }

    public DSpaceObjectDatasetGenerator(Node node) throws TransformerException {
        parseXML(node);
    }

    public int getType() {
        return type;
    }

    public void setType(int type) {
        this.type = type;
    }

    public DatasetQuery toDatasetQuery(Context context) {
        DatasetQuery datasetQuery = new DatasetQuery();
        datasetQuery.setMax(getMax());

        switch (type){
            case Constants.COMMUNITY:
                datasetQuery.setFacetField(getSolrField());
                datasetQuery.setLabel("Community");
                break;
            case Constants.COLLECTION:
                datasetQuery.setFacetField(getSolrField());
                datasetQuery.setLabel("Collection");
                break;
            case Constants.ITEM:
                datasetQuery.setFacetField(getSolrField());
                datasetQuery.setLabel("All Items");
                break;
            case Constants.BITSTREAM:
                datasetQuery.setFacetField(getSolrField());
                datasetQuery.setLabel("All Bitstreams");
                break;
            case Constants.SITE:
                datasetQuery.setLabel(ConfigurationManager.getProperty("dspace.name"));
                break;
        }

        return datasetQuery;
    }

    protected String getSolrField() {

        switch (type) {
            case Constants.COMMUNITY:
                return "containerCommunity";
            case Constants.COLLECTION:
                return "containerCollection";
            case Constants.ITEM:
                return isShareVersionStats() ? "version_id" : "containerItem";
            case Constants.BITSTREAM:
                return isShareVersionStats() ? "file_id" : "containerBitstream";
            case Constants.SITE:
                return ConfigurationManager.getProperty("dspace.name");
            default:
                return null;
        }
    }

    public void toXML(Document doc, Element root) {
        super.toXML(doc, root);

        root.setAttribute("type", DSpaceObjectDatasetGenerator.class.getName());

        Element type = doc.createElement("dsotype");
        root.appendChild(type);
        type.appendChild(doc.createTextNode("" + this.type));

        Element facetterm = doc.createElement("facetterm");
        root.appendChild(facetterm);
        facetterm.appendChild(doc.createTextNode("" + this.useFacetTerms));

        Element percentOfTotal = doc.createElement("percent-of-total");
        root.appendChild(percentOfTotal);
        percentOfTotal.appendChild(doc.createTextNode("" + this.percentOfTotal));

        Element splitByYear = doc.createElement("split-by-year");
        root.appendChild(splitByYear);
        splitByYear.appendChild(doc.createTextNode("" + this.splitByYear));

        if(getMax()>-1){
            Element limit = doc.createElement("limit");
            root.appendChild(limit);

            limit.setAttribute("type", "top");
            Element nNode = doc.createElement("n");
            limit.appendChild(nNode);
            nNode.appendChild(doc.createTextNode("" + getMax()));

        }

        Element columnLabel = doc.createElement("columnLabel");
        root.appendChild(splitByYear);
        columnLabel.appendChild(doc.createTextNode(getColumnLabel()));

    }

    public boolean isSplitByYear() {
        return splitByYear;
    }

    public void setSplitByYear(boolean splitByYear) {
        this.splitByYear = splitByYear;
    }

    public void parseXML(Node generatorNode) throws TransformerException {
        super.parseXML(generatorNode);

        Node showLinksNode = generatorNode.getAttributes().getNamedItem("showLinks");
        if (showLinksNode != null && "false".equals(showLinksNode.getNodeValue())) {
            this.showLinks = false;
        } else {
            this.showLinks = true;
        }

        Node typeNode = XPathAPI.selectSingleNode(generatorNode, "dsotype/text()");
        setType(Integer.parseInt(typeNode.getNodeValue()));

        Node facetTermNode = XPathAPI.selectSingleNode(generatorNode, "facetterm/text()");
        if(facetTermNode!=null){
            setUseFacetTerms("true".equalsIgnoreCase(facetTermNode.getNodeValue()));
        }

        Node perOfTotNode = XPathAPI.selectSingleNode(generatorNode, "percent-of-total/text()");
        if(perOfTotNode!=null){
            setPercentOfTotal("true".equalsIgnoreCase(perOfTotNode.getNodeValue()));
        }

        Node splitByYearNode = XPathAPI.selectSingleNode(generatorNode, "split-by-year/text()");
        if(splitByYearNode!=null){
            setSplitByYear("true".equalsIgnoreCase(splitByYearNode.getNodeValue()));
        }

        Node maxNode = XPathAPI.selectSingleNode(generatorNode, "limit[@type='top']/n/text()");
        if (maxNode != null){
            setMax(Integer.parseInt(maxNode.getNodeValue()));

        }
        else{
            setMax(-1);
        }

        Node columnLabel = XPathAPI.selectSingleNode(generatorNode, "column-label/text()");
        if (columnLabel != null) {
            setColumnLabel(columnLabel.getNodeValue());
        }
    }

    public boolean isPercentOfTotal() {
        return percentOfTotal;
    }

    public void setPercentOfTotal(boolean percentOfTotal) {
        this.percentOfTotal = percentOfTotal;
    }

    public int getMax() {
        return max;
    }

    public void setMax(int max) {
        this.max = max;
    }

    public String getGraphTitlePart() {
        switch (type){
            case Constants.COMMUNITY:
                return "Community";
            case Constants.COLLECTION:
                return "Collection";
            case Constants.ITEM:
                return "Item";
            case Constants.BITSTREAM:
                return "Bitstream";
            default:
                return null;
        }
    }

    public Dataset generate(Context context, Dataset dataset, DatasetTimeGenerator dateFacet, List<String> filterQuery, List<StatisticsFilter> filters, DSpaceObject currentDso, boolean showTotal) throws DeletedObjectRequiresRerunException, SQLException, ParseException, SolrServerException {

        DatasetQuery dataSetQuery = toDatasetQuery(context);
        String facetField = dataSetQuery.getFacetField();
        List<String> facetQueries = dataSetQuery.getFacetQueries();

        int max = dataSetQuery.getMax();
        if (dateFacet != null) {

            //We need to get the max objects and the next part of the query on them (next part beeing the datasettimequery
            if (facetField != null || CollectionUtils.isNotEmpty(facetQueries)) {

                List<String> facetTerms = null;

                if (useFacetTerms) {
                    for (StatisticsFilter filter : filters) {
                        if (filter instanceof StatisticsDsoFilter) {
                            StatisticsDsoFilter dsoFilter = (StatisticsDsoFilter) filter;
                            for (Integer id : dsoFilter.getIdsByType(this.type)) {
                                if (facetTerms == null) {
                                    facetTerms = new ArrayList<>();
                                }
                                facetTerms.add("" + id);
                            }
                        }
                    }
                }

                SolrLoggerParams params = new SolrLoggerParams();
                params.setQuery("*:*");
                params.setFilterQuery(filterQuery);
                params.setFacetFields(Collections.singletonList(facetField));
                params.setFacetQueries(facetQueries);
                params.setMax(max);
                params.setShowTotal(false);
                params.setFacetSort(true);

                ObjectCount[] maxObjectCounts;
                if (CollectionUtils.isEmpty(facetQueries)) {
                    maxObjectCounts = SolrLogger.queryFacetField(params);
                } else {
                    maxObjectCounts = SolrLogger.queryFacetQuery(params);
                }

                for (int j = 0; j < maxObjectCounts.length; j++) {
                    ObjectCount firstCount = maxObjectCounts[j];
                    String newQuery = facetField + ":\"" + ClientUtils.escapeQueryChars(firstCount.getValue())+"\"";
                    //Since we are querying on facet date no need for a max since our facets limit is forced by a filter query
                    ObjectCount[] maxDateFacetCounts = SolrLogger.queryFacetDate(newQuery, filterQuery, facetQueries, -1, dateFacet.getDateType(), dateFacet.getStartDate(), dateFacet.getEndDate(), showTotal);

                    //Make sure we have a dataSet
                    if (dataset == null)
                        dataset = new Dataset(maxObjectCounts.length, maxDateFacetCounts.length);
                    String value = firstCount.getValue();
                    Map<String,String> rowLabelAttr = new HashMap<String, String>();
                    String rlabel = SolrResultAttributesResolver.getResultName(value, getType(), getAttributesResolverField(), context);
                    dataset.setRowLabel(j, rlabel);
                    dataset.setRowLabelAttr(j,rowLabelAttr);

                    for (int k = 0; k < maxDateFacetCounts.length; k++) {
                        ObjectCount objectCount = maxDateFacetCounts[k];
                        //No need to add this many times
                        if (j == 0){
                            dataset.setColLabel(k, objectCount.getValue());
                            dataset.setColLabelAttr(k,"type","date");
                        }
                        dataset.addValueToMatrix(j, k, objectCount.getCount());
                        dataset.setCellAttr(j, k, "type","number");

                    }
                }
            } else {
                //Since we are querying on facet date no need for a max since our facets limit is forced by a filter query
                ObjectCount[] results = SolrLogger.queryFacetDate("*:*", filterQuery, facetQueries, -1, dateFacet.getDateType(), dateFacet.getStartDate(), dateFacet.getEndDate(), showTotal);

                dataset = new Dataset(1, results.length);
                //Now that we have our results put em in a matrix
                for (int j = 0; j < results.length; j++) {
                    dataset.setColLabel(j, results[j].getValue());
                    dataset.setColLabelAttr(j,"type","date");

                    dataset.addValueToMatrix(0, j, results[j].getCount());
                    dataset.setCellAttr(0, j, "type","number");

                }
                //TODO: change this !
                //Now add the column label
                try {
                    dataset.setRowLabel(0, SolrResultAttributesResolver.getResultName("" + -1, getType(), getAttributesResolverField(), context));
                } catch (IllegalStateException e) {
                    //We have an object that was deleted, remove it from solr & rerun the query
//                            SolrLogger.removeByQuery("type:" + generator.getType() + " AND id: " + -1, true);
//                            createDataset(context);
                }
                dataset.setRowLabelAttr(0, SolrResultAttributesResolver.getAttributes("" + -1, getType(), getAttributesResolverField(), currentDso, context));
            }


        } else {
            //We need to get the max objects and the next part of the query on them (next part beeing the datasettimequery
            String colLabel = getColumnLabel();
            if (facetField == null && CollectionUtils.isEmpty(facetQueries)) {
                QueryResponse queryResponse = SolrLogger.query("*:*", filterQuery, null, true, max, null, null, null, null);
                SolrDocumentList result = queryResponse.getResults();
                if (dataset == null)
                    dataset = new Dataset(1, 1);
                //Now that we have our results put em in a matrix
                dataset.setColLabel(0, colLabel);
                for (StatisticsFilter filter : filters) {
                    if (filter instanceof FilterWithLabel) {
                        String label = ((FilterWithLabel) filter).generateLabel();
                        if (label != null) {
                            dataset.setColLabel(0, label);
                            break;
                        }
                    }
                }
                dataset.addValueToMatrix(0, 0, result.getNumFound());
                dataset.setCellAttr(0, 0, "type", "number");

                try {
                    dataset.setRowLabel(0, StatisticsData.getResultName(-1, getType(), context));
                } catch (IllegalStateException e) {
                    //We have an object that was deleted, remove it from solr & rerun the query
//                            SolrLogger.removeByQuery("type:" + getType() + " AND id: " + -1, true);
//                            createDataset(context);
                }
                dataset.setRowLabelAttr(0, SolrResultAttributesResolver.getAttributes("" + -1, getType(), getAttributesResolverField(), currentDso, context));
            } else {
                SolrLoggerParams params = new SolrLoggerParams();
                params.setQuery("*:*");
                params.setFilterQuery(filterQuery);
                params.setFacetFields(Collections.singletonList(facetField));
                params.setFacetQueries(facetQueries);
                params.setMax(max +1);
                params.setShowTotal(false);
                params.setFacetSort(true);
                ObjectCount[] maxObjectCounts;
                if (CollectionUtils.isEmpty(facetQueries)) {
                    maxObjectCounts = SolrLogger.queryFacetField(params);
                } else {
                    maxObjectCounts = SolrLogger.queryFacetQuery(params);
                }


                boolean hasMore = false;
                if (maxObjectCounts.length > this.max) {
                    hasMore = true;
                    ArrayUtils.remove(maxObjectCounts, maxObjectCounts.length - 1);
                }
                //Make sure we have a dataSet
                if (dataset == null)
                    dataset = new Dataset(maxObjectCounts.length, 1);

                dataset.setHasMore(hasMore);

                for (int j = 0; j < maxObjectCounts.length; j++) {
                    ObjectCount firstCount = maxObjectCounts[j];

                    String value = firstCount.getValue();
                    if (showTotal && j == (maxObjectCounts.length - 1)) {
                        dataset.addValueToMatrix(j, 0, firstCount.getCount());
                        dataset.setCellAttr(j, 0, "type", "number");
                        dataset.setRowLabel(j, value);

                    } else {
                        String rlabel = SolrResultAttributesResolver.getResultName(value, getType(), getAttributesResolverField(), context);
                        dataset.setRowLabel(j, rlabel);
                        dataset.setColLabel(0, colLabel);
                        for (StatisticsFilter filter : filters) {
                            if (filter instanceof FilterWithLabel) {
                                String label = ((FilterWithLabel) filter).generateLabel();
                                if (label != null) {
                                    dataset.setColLabel(0, label);
                                    break;
                                }
                            }
                        }
                        dataset.addValueToMatrix(j, 0, firstCount.getCount());
                        dataset.setCellAttr(j, 0, "type", "number");
                        if (showLinks) {
                            dataset.setRowLabelAttr(j, SolrResultAttributesResolver.getAttributes(firstCount.getValue(), getType(), getAttributesResolverField(), currentDso, context));
                        }
                    }
                }
            }
        }

        if (dataset != null) {
            String label = dataSetQuery.getLabel();
            if (label != null) {
                dataset.setRowTitle(label);
            } else
                dataset.setRowTitle("Dataset");

        }

        return dataset;
    }

    protected String getAttributesResolverField() {
        return getSolrField();
    }


    public void setColumnLabel(String columnLabel) {
        this.columnLabel = columnLabel;
    }

    public String getColumnLabel() {
        return StringUtils.defaultIfBlank(columnLabel, "Overall");
    }
}
