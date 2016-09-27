<!--

    The contents of this file are subject to the license and copyright
    detailed in the LICENSE and NOTICE files at the root of the source
    tree and available online at

    http://www.dspace.org/license/

-->

<!--
    Rendering specific to the item display page.

    Author: art.lowel at atmire.com
    Author: lieven.droogmans at atmire.com
    Author: ben at atmire.com
    Author: Alexey Maslov

-->

<!-- File for the sole purpose of building the bulk of the DIM part of the item-view page
such as authors, subject, citation, description, etc
-->

<xsl:stylesheet
        xmlns:i18n="http://apache.org/cocoon/i18n/2.1"
        xmlns:dri="http://di.tamu.edu/DRI/1.0/"
        xmlns:mets="http://www.loc.gov/METS/"
        xmlns:dim="http://www.dspace.org/xmlns/dspace/dim"
        xmlns:xlink="http://www.w3.org/TR/xlink/"
        xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
        xmlns:atom="http://www.w3.org/2005/Atom"
        xmlns:ore="http://www.openarchives.org/ore/terms/"
        xmlns:oreatom="http://www.openarchives.org/ore/atom/"
        xmlns="http://www.w3.org/1999/xhtml"
        xmlns:xalan="http://xml.apache.org/xalan"
        xmlns:encoder="xalan://java.net.URLEncoder"
        xmlns:util="org.dspace.app.xmlui.utils.XSLUtils"
        xmlns:jstring="java.lang.String"
        xmlns:rights="http://cosimo.stanford.edu/sdr/metsrights/"
        xmlns:confman="org.dspace.core.ConfigurationManager"
        xmlns:url="http://whatever/java/java.net.URLEncoder"
        exclude-result-prefixes="xalan encoder i18n dri mets dim xlink xsl util jstring rights confman url">

    <xsl:output indent="yes"/>
    <xsl:template name="itemSummaryView-DIM-citation">
        <xsl:if test="dim:field[@element='identifier' and @qualifier='citation']">
            <div class="simple-item-view-description item-page-field-wrapper table">
                <h5 class="bold"><i18n:text>xmlui.dri2xhtml.METS-1.0.item-citation</i18n:text></h5>
                <div>
                    <xsl:for-each select="dim:field[@element='identifier' and @qualifier='citation']">
                        <xsl:choose>
                            <xsl:when test="node()">
                                <xsl:copy-of select="node()"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>&#160;</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:if test="count(following-sibling::dim:field[@element='identifier' and @qualifier='citation']) != 0">
                            <div class="spacer">&#160;</div>
                        </xsl:if>
                    </xsl:for-each>
                    <xsl:if test="count(dim:field[@element='identifier' and @qualifier='citation']) &gt; 1">
                        <div class="spacer">&#160;</div>
                    </xsl:if>
                </div>
            </div>
        </xsl:if>
    </xsl:template>


    <xsl:template name="itemSummaryView-DIM-notes">
        <xsl:if test="dim:field[@element='description'][not(@qualifier)]">
            <div class="simple-item-view-description item-page-field-wrapper table">
                <h5 class="bold"><i18n:text>xmlui.dri2xhtml.METS-1.0.item-notes</i18n:text></h5>
                <div>
                    <xsl:for-each select="dim:field[@element='description'][not(@qualifier)]">
                        <xsl:choose>
                            <xsl:when test="node()">
                                <xsl:copy-of select="node()"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>&#160;</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:if test="count(following-sibling::dim:field[@element='description'][not(@qualifier)]) != 0">
                            <div class="spacer">&#160;</div>
                        </xsl:if>
                    </xsl:for-each>
                    <xsl:if test="count(dim:field[@element='description'][not(@qualifier)] ) &gt; 1">
                        <div class="spacer">&#160;</div>
                    </xsl:if>
                </div>
            </div>
        </xsl:if>
    </xsl:template>
    <xsl:template name="itemSummaryView-DIM-affiliations">
        <xsl:if test="dim:field[@mdschema='cg' and @element='contributor' and @qualifier='crp']">
            <div class="simple-item-view-description item-page-field-wrapper table">
                <h5 class="bold"><i18n:text>xmlui.dri2xhtml.METS-1.0.item-affiliations</i18n:text></h5>
                <div>
                    <xsl:for-each select="dim:field[@mdschema='cg' and @element='contributor' and @qualifier='crp']">
                        <xsl:choose>
                            <xsl:when test="node()">
                                <xsl:call-template name="discovery-link">
                                    <xsl:with-param name="filtertype" select="'crpsubject'"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>&#160;</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:if test="count(following-sibling::dim:field[@mdschema='cg' and @element='contributor' and @qualifier='crp']) != 0">
                            <xsl:text>; </xsl:text>
                        </xsl:if>
                    </xsl:for-each>

                </div>
            </div>
        </xsl:if>
    </xsl:template>
    <xsl:template name="itemSummaryView-DIM-subject">
        <xsl:if test="dim:field[@element='subject' and not(@qualifier)]">
            <div class="simple-item-view-description item-page-field-wrapper table">
                <h5 class="bold"><i18n:text>xmlui.dri2xhtml.METS-1.0.item-agrovoc-terms</i18n:text></h5>
                <div>
                    <xsl:for-each select="dim:field[@element='subject' and not(@qualifier)]">
                        <xsl:choose>
                            <xsl:when test="node()">
                                <xsl:call-template name="discovery-link">
                                    <xsl:with-param name="filtertype" select="'subject'"/>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>&#160;</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:if test="count(following-sibling::dim:field[@element='subject' and not(@qualifier)]) != 0">
                            <xsl:text>; </xsl:text>
                        </xsl:if>
                    </xsl:for-each>

                </div>
            </div>
        </xsl:if>
    </xsl:template>
    <xsl:template name="itemSummaryView-DIM-investors-sponsors">
        <xsl:if test="dim:field[@element='description' and @qualifier='sponsorship']">
            <div class="word-break item-page-field-wrapper table">
                <h5 class="bold">
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.item-investors-sponsors</i18n:text>
                </h5>
                <xsl:for-each select="dim:field[@element='description' and @qualifier='sponsorship' ]">
                    <a target="_blank" >
                        <xsl:attribute name="href">
                            <xsl:value-of select="concat($context-path,'/discover?filtertype=sponsorship&amp;filter_relational_operator=equals&amp;filter=',url:encode(node()))"></xsl:value-of>
                        </xsl:attribute>
                        <xsl:copy-of select="./node()"/>
                    </a>
                    <xsl:if test="count(following-sibling::dim:field[@element='description' and @qualifier='sponsorship']) != 0">
                        <xsl:text>; </xsl:text>
                    </xsl:if>
                </xsl:for-each>
            </div>
        </xsl:if>
    </xsl:template>
    <xsl:template name="itemSummaryView-DIM-identifiers">
        <xsl:if test="dim:field[@element='identifier' and @qualifier='uri']">
            <div class="simple-item-view-description item-page-field-wrapper table">
                <xsl:call-template name="itemSummaryView-DIM-permanenturi"/>
                <xsl:call-template name="itemSummaryView-DIM-interneturl"/>
                <xsl:call-template name="itemSummaryView-DIM-googleurl"/>
                <xsl:call-template name="itemSummaryView-DIM-doi"/>
            </div>

        </xsl:if>
    </xsl:template>
    <xsl:template name="itemSummaryView-DIM-related-material">
        <xsl:if test="dim:field[@mdschema='cg' and @element='link' ] or dim:field[@mdschema='cg' and @element='identifier' and @qualifier='dataurl' ]">
            <div class="simple-item-view-description item-page-field-wrapper table">
                <h5 class="bold">
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.item-related-material</i18n:text>
                </h5>
                <div class="marginleft">
                <xsl:call-template name="itemSummaryView-DIM-datafile"/>
                <xsl:call-template name="itemSummaryView-DIM-videolink"/>
                <xsl:call-template name="itemSummaryView-DIM-audiolink"/>
                <xsl:call-template name="itemSummaryView-DIM-photolink"/>
                <xsl:call-template name="itemSummaryView-DIM-referencelink"/>
                </div>
            </div>
        </xsl:if>
    </xsl:template>

    <xsl:template name="itemSummaryView-DIM-abstract">
        <xsl:if test="dim:field[@element='description' and @qualifier='abstract']">
            <div class="simple-item-view-description item-page-field-wrapper table">
                <h5 class="bold"><i18n:text>xmlui.dri2xhtml.METS-1.0.item-abstract</i18n:text></h5>
                <div>
                    <xsl:for-each select="dim:field[@element='description' and @qualifier='abstract']">
                        <xsl:choose>
                            <xsl:when test="node()">
                                <xsl:copy-of select="node()"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>&#160;</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:if test="count(following-sibling::dim:field[@element='description' and @qualifier='abstract']) != 0">
                            <div class="spacer">&#160;</div>
                        </xsl:if>
                    </xsl:for-each>
                    <xsl:if test="count(dim:field[@element='description' and @qualifier='abstract']) &gt; 1">
                        <div class="spacer">&#160;</div>
                    </xsl:if>
                </div>
            </div>
        </xsl:if>
    </xsl:template>

    <xsl:template name="itemSummaryView-DIM-authors">
        <xsl:if test="dim:field[@element='contributor'][@qualifier='author' and descendant::text()] or dim:field[@element='creator' and descendant::text()] or dim:field[@element='contributor' and descendant::text()]">
            <div class="simple-item-view-authors item-page-field-wrapper table">
                <h5 class="bold"><i18n:text>xmlui.dri2xhtml.METS-1.0.item-author</i18n:text></h5>
                <xsl:choose>
                    <xsl:when test="dim:field[@element='contributor'][@qualifier='author']">
                        <xsl:for-each select="dim:field[@element='contributor'][@qualifier='author']">
                            <xsl:call-template name="itemSummaryView-DIM-authors-entry" />
                        </xsl:for-each>
                    </xsl:when>
                    <xsl:when test="dim:field[@element='creator']">
                        <xsl:for-each select="dim:field[@element='creator']">
                            <xsl:call-template name="itemSummaryView-DIM-authors-entry" />
                        </xsl:for-each>
                    </xsl:when>
                    <xsl:when test="dim:field[@element='contributor']">
                        <xsl:for-each select="dim:field[@element='contributor']">
                            <xsl:call-template name="itemSummaryView-DIM-authors-entry" />
                        </xsl:for-each>
                    </xsl:when>
                    <xsl:otherwise>
                        <i18n:text>xmlui.dri2xhtml.METS-1.0.no-author</i18n:text>
                    </xsl:otherwise>
                </xsl:choose>
            </div>
        </xsl:if>
    </xsl:template>

    <xsl:template name="itemSummaryView-DIM-authors-entry">
        <div>
            <xsl:if test="@authority">
                <xsl:attribute name="class"><xsl:text>ds-dc_contributor_author-authority</xsl:text></xsl:attribute>
            </xsl:if>
            <xsl:call-template name="discovery-link">
                <xsl:with-param name="filtertype" select="'author'"/>
            </xsl:call-template>

            <xsl:if test="@authority">
	            <xsl:variable name="authority" select="@authority"/>

	            <xsl:if test="../dim:field[@authority=$authority and @mdschema='atmire' and @element='orcid' and @qualifier='id']">
		            <a class="orcid-icon-link" target="_blank">
			            <xsl:attribute name="href">
				            <xsl:value-of select="concat('//orcid.org/', ../dim:field[@authority=$authority and @mdschema='atmire' and @element='orcid' and @qualifier='id']/text())"/>
			            </xsl:attribute>

			            <img alt="xmlui.mirage2.item-list.thumbnail" i18n:attr="alt"
			                 src="{concat($theme-path, 'images/mini-icon.png')}"/>
		            </a>
	            </xsl:if>
            </xsl:if>
        </div>
    </xsl:template>

    <xsl:template name="itemSummaryView-DIM-URI">
        <xsl:if test="dim:field[@element='identifier' and @qualifier='uri' and descendant::text()]">
            <div class="item-page-field-wrapper table">
                <h5><i18n:text>xmlui.dri2xhtml.METS-1.0.item-uri</i18n:text></h5>
                <span>
                    <xsl:for-each select="dim:field[@element='identifier' and @qualifier='uri']">
                        <a>
                            <xsl:attribute name="href">
                                <xsl:copy-of select="./node()"/>
                            </xsl:attribute>
                            <xsl:copy-of select="./node()"/>
                        </a>
                        <xsl:if test="count(following-sibling::dim:field[@element='identifier' and @qualifier='uri']) != 0">
                            <br/>
                        </xsl:if>
                    </xsl:for-each>
                </span>
            </div>
        </xsl:if>
    </xsl:template>

    <xsl:template name="itemSummaryView-DIM-date">
        <xsl:if test="dim:field[@element='date' and @qualifier='issued' and descendant::text()]">
            <div class="simple-item-view-date word-break item-page-field-wrapper table">
                <h5 class="bold">
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.item-date</i18n:text>
                </h5>
                <xsl:for-each select="dim:field[@element='date' and @qualifier='issued']">
                    <xsl:variable name="date">
                        <xsl:value-of
                                select="substring(./node(),1,10)"/>
                    </xsl:variable>
                    <xsl:variable name="year" select="substring($date, 1, 4)"/>
                    <xsl:variable name="month" select="substring($date, 6, 2)"/>
                    <xsl:value-of select="$year"/>

                    <xsl:if test="$month">
                        <xsl:text>-</xsl:text>
                        <xsl:value-of select="$month"/>
                    </xsl:if>
                    <xsl:if test="count(following-sibling::dim:field[@element='date' and @qualifier='issued']) != 0">
                        <br/>
                    </xsl:if>
                </xsl:for-each>
            </div>
        </xsl:if>
    </xsl:template>
    <xsl:template name="itemSummaryView-DIM-subjects">
        <xsl:variable name="subjectTest">
            <xsl:value-of select="dim:field[@mdschema='cg' and @element='subject' and @qualifier='ccafs']
        or dim:field[@mdschema='cg' and @element='subject' and @qualifier='cifor']
        or dim:field[@mdschema='cg' and @element='subject' and @qualifier='cpwf']
        or dim:field[@mdschema='cg' and @element='subject' and @qualifier='ilri']
        or dim:field[@mdschema='cg' and @element='subject' and @qualifier='iwmi']
        or dim:field[@mdschema='cg' and @element='subject' and @qualifier='bioversity']
        or dim:field[@mdschema='cg' and @element='subject' and @qualifier='ciat']
        or dim:field[@mdschema='cg' and @element='subject' and @qualifier='cip']
        or dim:field[@mdschema='cg' and @element='subject' and @qualifier='cta']
        or dim:field[@mdschema='cg' and @element='subject' and @qualifier='drylands']
        or dim:field[@mdschema='cg' and @element='subject' and @qualifier='humidtropics']
        or dim:field[@mdschema='cg' and @element='subject' and @qualifier='icarda']
        or dim:field[@mdschema='cg' and @element='subject' and @qualifier='iita']
        or dim:field[@mdschema='cg' and @element='subject' and @qualifier='wle']"/>
        </xsl:variable>

        <xsl:if test="$subjectTest ='true'">
            <div class="word-break item-page-field-wrapper table">
                <h5 class="bold">
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.item-subject</i18n:text>
                </h5>
                <span class="cgiar-subjects">
                    <xsl:call-template name="bioversitysubject"/>
                    <xsl:call-template name="ccafsubject"/>
                    <xsl:call-template name="ciatsubject"/>
                    <xsl:call-template name="ciforsubject"/>
                    <xsl:call-template name="cipsubject"/>
                    <xsl:call-template name="cpwfsubject"/>
                    <xsl:call-template name="ctasubject"/>
                    <xsl:call-template name="drylandssubject"/>
                    <xsl:call-template name="humidtropicssubject"/>
                    <xsl:call-template name="icardasubject"/>
                    <xsl:call-template name="iitasubject"/>
                    <xsl:call-template name="ilrisubject"/>
                    <xsl:call-template name="iwmisubject"/>
                    <!-- the last template called should not output ";" at the end -->
                    <xsl:call-template name="wlesubject"/>
                </span>
            </div>
        </xsl:if>
    </xsl:template>

    <!--Helper template that creates a link to the discovery page based on a given node and filtertype to inject into the link-->
    <xsl:template name="discovery-link">
        <xsl:param name="filtertype"/>
        <xsl:variable name="filterlink">
            <xsl:value-of select="concat($context-path,'/discover?filtertype=',$filtertype,'&amp;filter_relational_operator=equals&amp;filter=',url:encode(node()))"></xsl:value-of>
        </xsl:variable>
        <a target="_blank">
            <xsl:attribute name="href" >
                <xsl:value-of select="$filterlink"/>
            </xsl:attribute>
            <xsl:copy-of select="node()"/>
        </a>
    </xsl:template>

    <xsl:template name="ccafsubject">
        <xsl:if test="dim:field[@mdschema='cg' and @element='subject' and @qualifier='ccafs']">
            <xsl:for-each select="dim:field[@mdschema='cg' and @element='subject' and @qualifier='ccafs']">
                <xsl:call-template name="discovery-link">
                    <xsl:with-param name="filtertype" select="'ccafsubject'"/>
                </xsl:call-template>
                    <xsl:text>; </xsl:text>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <xsl:template name="ciforsubject">
        <xsl:if test="dim:field[@mdschema='cg' and @element='subject' and @qualifier='cifor']">
            <xsl:for-each select="dim:field[@mdschema='cg' and @element='subject' and @qualifier='cifor']">
                <xsl:call-template name="discovery-link">
                    <xsl:with-param name="filtertype" select="'ccafsubject'"/>
                </xsl:call-template>
                    <xsl:text>; </xsl:text>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <xsl:template name="cpwfsubject">
        <xsl:if test="dim:field[@mdschema='cg' and @element='subject' and @qualifier='cpwf']">
            <xsl:for-each select="dim:field[@mdschema='cg' and @element='subject' and @qualifier='cpwf']">
                <xsl:call-template name="discovery-link">
                    <xsl:with-param name="filtertype" select="'cpwfsubject'"/>
                </xsl:call-template>
                    <xsl:text>; </xsl:text>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <xsl:template name="ilrisubject">
        <xsl:if test="dim:field[@mdschema='cg' and @element='subject' and @qualifier='ilri']">
            <xsl:for-each select="dim:field[@mdschema='cg' and @element='subject' and @qualifier='ilri']">
                <xsl:call-template name="discovery-link">
                    <xsl:with-param name="filtertype" select="'ilrisubject'"/>
                </xsl:call-template>
                    <xsl:text>; </xsl:text>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <xsl:template name="iwmisubject">
        <xsl:if test="dim:field[@mdschema='cg' and @element='subject' and @qualifier='iwmi']">
            <xsl:for-each select="dim:field[@mdschema='cg' and @element='subject' and @qualifier='iwmi']">
                <xsl:call-template name="discovery-link">
                    <xsl:with-param name="filtertype" select="'iwmisubject'"/>
                </xsl:call-template>
                    <xsl:text>; </xsl:text>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <xsl:template name="wlesubject">
        <xsl:if test="dim:field[@mdschema='cg' and @element='subject' and @qualifier='wle']">
            <xsl:for-each select="dim:field[@mdschema='cg' and @element='subject' and @qualifier='wle']">
                <xsl:call-template name="discovery-link">
                    <xsl:with-param name="filtertype" select="'wlesubject'"/>
                </xsl:call-template>
                <xsl:if test="count(following-sibling::dim:field[@mdschema='cg' and @element='subject' and @qualifier='wle']) != 0">
                    <xsl:text>; </xsl:text>
                </xsl:if>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <xsl:template name="cipsubject">
        <xsl:if test="dim:field[@mdschema='cg' and @element='subject' and @qualifier='cip']">
            <xsl:for-each select="dim:field[@mdschema='cg' and @element='subject' and @qualifier='cip']">
                <xsl:call-template name="discovery-link">
                    <xsl:with-param name="filtertype" select="'cipsubject'"/>
                </xsl:call-template>
                    <xsl:text>; </xsl:text>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <xsl:template name="drylandssubject">
        <xsl:if test="dim:field[@mdschema='cg' and @element='subject' and @qualifier='drylands']">
            <xsl:for-each select="dim:field[@mdschema='cg' and @element='subject' and @qualifier='drylands']">
                <xsl:call-template name="discovery-link">
                    <xsl:with-param name="filtertype" select="'drylandssubject'"/>
                </xsl:call-template>
                    <xsl:text>; </xsl:text>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <xsl:template name="icardasubject">
        <xsl:if test="dim:field[@mdschema='cg' and @element='subject' and @qualifier='icarda']">
            <xsl:for-each select="dim:field[@mdschema='cg' and @element='subject' and @qualifier='icarda']">
                <xsl:call-template name="discovery-link">
                    <xsl:with-param name="filtertype" select="'icardasubject'"/>
                </xsl:call-template>
                    <xsl:text>; </xsl:text>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <xsl:template name="bioversitysubject">
        <xsl:if test="dim:field[@mdschema='cg' and @element='subject' and @qualifier='bioversity']">
            <xsl:for-each select="dim:field[@mdschema='cg' and @element='subject' and @qualifier='bioversity']">
                <xsl:call-template name="discovery-link">
                    <xsl:with-param name="filtertype" select="'bioversitysubject'"/>
                </xsl:call-template>
                    <xsl:text>; </xsl:text>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <xsl:template name="ciatsubject">
        <xsl:if test="dim:field[@mdschema='cg' and @element='subject' and @qualifier='ciat']">
            <xsl:for-each select="dim:field[@mdschema='cg' and @element='subject' and @qualifier='ciat']">
                <xsl:call-template name="discovery-link">
                    <xsl:with-param name="filtertype" select="'ciatsubject'"/>
                </xsl:call-template>
                    <xsl:text>; </xsl:text>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <xsl:template name="ctasubject">
        <xsl:if test="dim:field[@mdschema='cg' and @element='subject' and @qualifier='cta']">
            <xsl:for-each select="dim:field[@mdschema='cg' and @element='subject' and @qualifier='cta']">
                <xsl:call-template name="discovery-link">
                    <xsl:with-param name="filtertype" select="'ctasubject'"/>
                </xsl:call-template>
                    <xsl:text>; </xsl:text>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <xsl:template name="humidtropicssubject">
        <xsl:if test="dim:field[@mdschema='cg' and @element='subject' and @qualifier='humidtropics']">
            <xsl:for-each select="dim:field[@mdschema='cg' and @element='subject' and @qualifier='humidtropics']">
                <xsl:call-template name="discovery-link">
                    <xsl:with-param name="filtertype" select="'humidtropicssubject'"/>
                </xsl:call-template>
                    <xsl:text>; </xsl:text>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <xsl:template name="iitasubject">
        <xsl:if test="dim:field[@mdschema='cg' and @element='subject' and @qualifier='iita']">
            <xsl:for-each select="dim:field[@mdschema='cg' and @element='subject' and @qualifier='iita']">
                <xsl:call-template name="discovery-link">
                    <xsl:with-param name="filtertype" select="'iitasubject'"/>
                </xsl:call-template>
                <xsl:if test="count(following-sibling::dim:field[@mdschema='cg' and @element='subject' and @qualifier='iita']) != 0">
                    <xsl:text>; </xsl:text>
                </xsl:if>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>


    <xsl:template name="itemSummaryView-DIM-countries">
        <xsl:if test="dim:field[@mdschema='cg' and @element='coverage' and @qualifier='country' and descendant::text()]">
            <div class="word-break item-page-field-wrapper table">
                <h5 class="bold">
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.item-countries</i18n:text>
                </h5>
                <xsl:for-each select="dim:field[@mdschema='cg' and @element='coverage' and @qualifier='country' ]">
                    <a target="_blank" >
                        <xsl:attribute name="href">
                            <xsl:value-of select="concat($context-path,'/discover?filtertype=country&amp;filter_relational_operator=equals&amp;filter=',url:encode(node()))"></xsl:value-of>
                        </xsl:attribute>
                        <xsl:copy-of select="./node()"/>
                    </a>
                    <xsl:if test="count(following-sibling::dim:field[@mdschema='cg' and @element='coverage' and @qualifier='country']) != 0">
                        <xsl:text>; </xsl:text>
                    </xsl:if>
                </xsl:for-each>
            </div>
        </xsl:if>

    </xsl:template>
    <xsl:template name="itemSummaryView-DIM-regions">
        <xsl:if test="dim:field[@mdschema='cg' and @element='coverage' and @qualifier='region' and descendant::text()]">
            <div class="word-break item-page-field-wrapper table">
                <h5 class="bold">
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.item-regions</i18n:text>
                </h5>
                <xsl:for-each select="dim:field[@mdschema='cg' and @element='coverage' and @qualifier='region' ]">
                    <a target="_blank" >
                        <xsl:attribute name="href">
                            <xsl:value-of select="concat($context-path,'/discover?filtertype=region&amp;filter_relational_operator=equals&amp;filter=',url:encode(node()))"></xsl:value-of>
                        </xsl:attribute>
                        <xsl:copy-of select="./node()"/>
                    </a>
                    <xsl:if test="count(following-sibling::dim:field[@mdschema='cg' and @element='coverage' and @qualifier='region']) != 0">
                        <xsl:text>; </xsl:text>
                    </xsl:if>
                </xsl:for-each>
            </div>
        </xsl:if>

    </xsl:template>
    <xsl:template name="itemSummaryView-DIM-species">
        <xsl:if test="dim:field[@mdschema='cg' and @element='species' and not(@qualifier)]">
            <div class="word-break item-page-field-wrapper table">
                <h5 class="bold">
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.item-species</i18n:text>
                </h5>
                <xsl:for-each select="dim:field[@mdschema='cg' and @element='species' and not(@qualifier)]">
                    <a target="_blank" >
                        <xsl:attribute name="href">
                            <xsl:value-of select="concat($context-path,'/discover?filtertype=species&amp;filter_relational_operator=equals&amp;filter=',url:encode(node()))"></xsl:value-of>
                        </xsl:attribute>
                        <xsl:copy-of select="./node()"/>
                    </a>
                    <xsl:if test="count(following-sibling::dim:field[@mdschema='cg' and @element='species' and not(@qualifier)]) != 0">
                        <xsl:text>; </xsl:text>
                    </xsl:if>
                </xsl:for-each>
            </div>
        </xsl:if>
    </xsl:template>
    <xsl:template name="itemSummaryView-DIM-breeds">
        <xsl:if test="dim:field[@mdschema='cg' and @element='species' and @qualifier='breed' and descendant::text()]">
            <div class="word-break item-page-field-wrapper table">
                <h5 class="bold">
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.item-breeds</i18n:text>
                </h5>
                <xsl:for-each select="dim:field[@mdschema='cg' and @element='species' and @qualifier='breed' ]">
                    <a target="_blank" >
                        <xsl:attribute name="href">
                            <xsl:value-of select="concat($context-path,'/discover?filtertype=breed&amp;filter_relational_operator=equals&amp;filter=',url:encode(node()))"></xsl:value-of>
                        </xsl:attribute>
                        <xsl:copy-of select="./node()"/>
                    </a>
                    <xsl:if test="count(following-sibling::dim:field[@mdschema='cg' and @element='species' and @qualifier='breed']) != 0">
                        <xsl:text>; </xsl:text>
                    </xsl:if>
                </xsl:for-each>
            </div>
        </xsl:if>
    </xsl:template>

    <xsl:template name="itemSummaryView-DIM-language">
        <xsl:if test="dim:field[@element='language' and @qualifier='iso' and descendant::text()]">
            <div class="word-break item-page-field-wrapper table">
                <h5 class="bold">
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.item-language</i18n:text>
                </h5>
                <xsl:for-each select="dim:field[@element='language' and @qualifier='iso' ]">
                    <xsl:copy-of select="node()"/>
                    <xsl:if test="count(following-sibling::dim:field[@element='language' and @qualifier='iso'] ) != 0">
                        <xsl:text>; </xsl:text>
                    </xsl:if>
                </xsl:for-each>
            </div>
        </xsl:if>

    </xsl:template>
    <xsl:template name="itemSummaryView-DIM-type">
        <xsl:if test="dim:field[@element='type' and descendant::text()]">
            <div class="word-break item-page-field-wrapper table">
                <h5 class="bold">
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.item-type</i18n:text>
                </h5>
                <xsl:for-each select="dim:field[@element='type']">
                    <a target="_blank" >
                        <xsl:attribute name="href">
                            <xsl:value-of select="concat($context-path,'/discover?filtertype=type&amp;filter_relational_operator=equals&amp;filter=',url:encode(node()))"></xsl:value-of>
                        </xsl:attribute>
                        <xsl:copy-of select="./node()"/>
                    </a>                    <xsl:if test="count(following-sibling::dim:field[@element='type'] ) != 0">
                    <xsl:text>; </xsl:text>
                </xsl:if>
                </xsl:for-each>
            </div>
        </xsl:if>


    </xsl:template>
    <xsl:template name="itemSummaryView-DIM-review-status">
        <xsl:if test="dim:field[@element='description' and @qualifier='version' and descendant::text()]">
            <div class=" word-break item-page-field-wrapper table">
                <h5 class="bold">
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.item-review-status</i18n:text>
                </h5>
                <xsl:for-each select="dim:field[@element='description' and @qualifier='version' ]">
                    <xsl:copy-of select="./node()"/>
                    <xsl:if test="count(following-sibling::dim:field[@element='description' and @qualifier='version'] ) != 0">
                        <xsl:text>; </xsl:text>
                    </xsl:if>
                </xsl:for-each>
            </div>
        </xsl:if>

    </xsl:template>
    <xsl:template name="itemSummaryView-DIM-accessibility">
        <xsl:if test="dim:field[@mdschema='cg' and @element='identifier' and @qualifier='status' and descendant::text()]">
            <div class=" word-break item-page-field-wrapper table">
                <h5 class="bold">
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.item-accessibility</i18n:text>
                </h5>
                <xsl:for-each select="dim:field[@mdschema='cg' and @element='identifier' and @qualifier='status' ]">
                    <xsl:copy-of select="./node()"/>
                    <xsl:if test="count(following-sibling::dim:field[@mdschema='cg' and @element='identifier' and @qualifier='status'] ) != 0">
                        <xsl:text>; </xsl:text>
                    </xsl:if>
                </xsl:for-each>
            </div>
        </xsl:if>

    </xsl:template>

    <xsl:template name="itemSummaryView-show-full">
        <div class="simple-item-view-show-full item-page-field-wrapper table">
            <h5 class="bold">
                <i18n:text>xmlui.mirage2.itemSummaryView.MetaData</i18n:text>
            </h5>
            <a>
                <xsl:attribute name="href"><xsl:value-of select="$ds_item_view_toggle_url"/></xsl:attribute>
                <i18n:text>xmlui.ArtifactBrowser.ItemViewer.show_full</i18n:text>
            </a>
        </div>
    </xsl:template>

    <xsl:template name="itemSummaryView-sharing">
        <div class="item-page-field-wrapper table">
            <h5 class="bold">
                Share
            </h5>
            <a>
                <xsl:attribute name="href"><xsl:text>https://twitter.com/home?status=</xsl:text><xsl:value-of select="dim:field[@element='identifier' and @qualifier='uri']"/></xsl:attribute>
                <xsl:attribute name="title"><xsl:text>Tweet this</xsl:text></xsl:attribute>
                <xsl:attribute name="target"><xsl:text>blank</xsl:text></xsl:attribute>
                <span class="fa fa-twitter-square fa-2x"></span>
            </a>
            <a>
                <xsl:attribute name="href"><xsl:text>https://www.facebook.com/sharer/sharer.php?u=</xsl:text><xsl:value-of select="dim:field[@element='identifier' and @qualifier='uri']"/></xsl:attribute>
                <xsl:attribute name="title"><xsl:text>Share on Facebook</xsl:text></xsl:attribute>
                <xsl:attribute name="target"><xsl:text>blank</xsl:text></xsl:attribute>
                <span class="fa fa-facebook-square fa-2x" aria-hidden="true"></span>
            </a>
            <a>
                <xsl:attribute name="href"><xsl:text>https://plus.google.com/share?url=</xsl:text><xsl:value-of select="dim:field[@element='identifier' and @qualifier='uri']"/></xsl:attribute>
                <xsl:attribute name="title"><xsl:text>Share on Google+</xsl:text></xsl:attribute>
                <xsl:attribute name="target"><xsl:text>blank</xsl:text></xsl:attribute>
                <span class="fa fa-google-plus-square fa-2x" aria-hidden="true"></span>
            </a>
            <a>
                <xsl:attribute name="href"><xsl:text>https://www.linkedin.com/shareArticle?mini=true&amp;url=</xsl:text><xsl:value-of select="dim:field[@element='identifier' and @qualifier='uri']"/></xsl:attribute>
                <xsl:attribute name="title"><xsl:text>Share on LinkedIn</xsl:text></xsl:attribute>
                <xsl:attribute name="target"><xsl:text>blank</xsl:text></xsl:attribute>
                <span class="fa fa-linkedin-square fa-2x" aria-hidden="true"></span>
            </a>
            <a>
                <xsl:attribute name="href"><xsl:text>https://delicious.com/save?v=5&amp;provider=CGSpace&amp;noui&amp;jump=close&amp;url=</xsl:text><xsl:value-of select="dim:field[@element='identifier' and @qualifier='uri']"/></xsl:attribute>
                <xsl:attribute name="title"><xsl:text>Save this on Delicious</xsl:text></xsl:attribute>
                <xsl:attribute name="target"><xsl:text>_blank</xsl:text></xsl:attribute>
                <span class="fa fa-delicious fa-2x" aria-hidden="true"></span>
            </a>
            <a>
                <xsl:attribute name="href"><xsl:text>https://www.mendeley.com/import/?url=</xsl:text><xsl:value-of select="dim:field[@element='identifier' and @qualifier='uri']"/></xsl:attribute>
                <xsl:attribute name="title"><xsl:text>Add this article to your Mendeley library</xsl:text></xsl:attribute>
                <xsl:attribute name="target"><xsl:text>blank</xsl:text></xsl:attribute>
                <span class="ai ai-mendeley-square ai-2x" aria-hidden="true"></span>
            </a>
            <a>
                <xsl:attribute name="href"><xsl:text>mailto:?&amp;body=</xsl:text><xsl:value-of select="dim:field[@element='identifier' and @qualifier='uri']"/><xsl:text>&amp;media=&amp;description=</xsl:text></xsl:attribute>
                <xsl:attribute name="title"><xsl:text>Share via e-mail</xsl:text></xsl:attribute>
                <span class="fa fa-envelope fa-2x" aria-hidden="true"></span>
            </a>
        </div>
    </xsl:template>



  <!--Start related matieral -->
    <xsl:template name="itemSummaryView-DIM-datafile">
        <xsl:if test="dim:field[@mdschema='cg' and @element='identifier' and @qualifier='dataurl' ]">
            <div>
                <span>
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.item-related-datafile</i18n:text>
                </span>

                <span >
                    <xsl:for-each select="dim:field[@mdschema='cg' and @element='identifier' and @qualifier='dataurl']">
                        <xsl:choose>
                            <xsl:when test="node()">
                                <a target="_blank">
                                    <xsl:attribute name="href">
                                        <xsl:copy-of select="./node()"/>
                                    </xsl:attribute>
                                    <xsl:copy-of select="./node()"/>
                                </a>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>&#160;</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:if test="count(following-sibling::dim:field[ @mdschema='cg' and @element='identifier' and @qualifier='dataurl']) != 0">
                            <xsl:text>; </xsl:text>
                        </xsl:if>
                    </xsl:for-each>
                    <xsl:if test="count(dim:field[@mdschema='cg' and @element='identifier' and @qualifier='dataurl'] ) &gt; 1">
                        <div class="spacer">&#160;</div>
                    </xsl:if>
                </span>
            </div>
        </xsl:if>
    </xsl:template>
    <xsl:template name="itemSummaryView-DIM-videolink">

        <xsl:if test="dim:field[@mdschema='cg' and @element='link' and @qualifier='video' ]">
            <div>
                <span>
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.item-related-video</i18n:text>
                </span>
                <span >
                    <xsl:for-each select="dim:field[@mdschema='cg' and @element='link' and @qualifier='video']">
                        <xsl:choose>
                            <xsl:when test="node()">
                                <a target="_blank">
                                    <xsl:attribute name="href">
                                        <xsl:copy-of select="./node()"/>
                                    </xsl:attribute>
                                    <xsl:copy-of select="./node()"/>
                                </a>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>&#160;</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:if test="count(following-sibling::dim:field[@mdschema='cg' and  @element='link' and @qualifier='video']) != 0">
                            <xsl:text>; </xsl:text>
                        </xsl:if>
                    </xsl:for-each>
                    <xsl:if test="count(dim:field[@mdschema='cg' and @element='link' and @qualifier='video'] ) &gt; 1">
                        <div class="spacer">&#160;</div>
                    </xsl:if>
                </span>
            </div>
        </xsl:if>
    </xsl:template>
    <xsl:template name="itemSummaryView-DIM-audiolink">
        <xsl:if test="dim:field[@mdschema='cg' and @element='link' and @qualifier='audio' ]">
            <div>
                <span>
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.item-related-audio</i18n:text>
                </span>

                <span >
                    <xsl:for-each select="dim:field[@mdschema='cg' and @element='link' and @qualifier='audio']">
                        <xsl:choose>
                            <xsl:when test="node()">
                                <a target="_blank">
                                    <xsl:attribute name="href">
                                        <xsl:copy-of select="./node()"/>
                                    </xsl:attribute>
                                    <xsl:copy-of select="./node()"/>
                                </a>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>&#160;</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:if test="count(following-sibling::dim:field[@mdschema='cg' and  @element='link' and @qualifier='audio']) != 0">
                            <xsl:text>; </xsl:text>
                        </xsl:if>
                    </xsl:for-each>
                    <xsl:if test="count(dim:field[@mdschema='cg' and @element='link' and @qualifier='audio'] ) &gt; 1">
                        <div class="spacer">&#160;</div>
                    </xsl:if>
                </span>
            </div>
        </xsl:if>
    </xsl:template>
    <xsl:template name="itemSummaryView-DIM-photolink">
        <xsl:if test="dim:field[@mdschema='cg' and @element='link' and @qualifier='photo' ]">
            <div>
                <span>
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.item-related-photo</i18n:text>

                </span>

                <span >
                    <xsl:for-each select="dim:field[@mdschema='cg' and @element='link' and @qualifier='photo']">
                        <xsl:choose>
                            <xsl:when test="node()">
                                <a target="_blank">
                                    <xsl:attribute name="href">
                                        <xsl:copy-of select="./node()"/>
                                    </xsl:attribute>
                                    <xsl:copy-of select="./node()"/>
                                </a>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>&#160;</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:if test="count(following-sibling::dim:field[@mdschema='cg' and  @element='link' and @qualifier='photo']) != 0">
                            <xsl:text>; </xsl:text>
                        </xsl:if>
                    </xsl:for-each>
                    <xsl:if test="count(dim:field[@mdschema='cg' and @element='link' and @qualifier='photo'] ) &gt; 1">
                        <div class="spacer">&#160;</div>
                    </xsl:if>
                </span>
            </div>
        </xsl:if>
    </xsl:template>
    <xsl:template name="itemSummaryView-DIM-referencelink">
        <xsl:if test="dim:field[@mdschema='cg' and @element='link' and @qualifier='reference' ]">
            <div>
                <span>
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.item-related-reference</i18n:text>
                </span>

                <span >
                    <xsl:for-each select="dim:field[@mdschema='cg' and @element='link' and @qualifier='reference']">
                        <xsl:choose>
                            <xsl:when test="node()">
                                <a target="_blank">
                                    <xsl:attribute name="href">
                                        <xsl:copy-of select="./node()"/>
                                    </xsl:attribute>
                                    <xsl:copy-of select="./node()"/>
                                </a>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>&#160;</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:if test="count(following-sibling::dim:field[@mdschema='cg' and  @element='link' and @qualifier='reference']) != 0">
                            <xsl:text>; </xsl:text>
                        </xsl:if>
                    </xsl:for-each>
                    <xsl:if test="count(dim:field[@mdschema='cg' and @element='link' and @qualifier='reference'] ) &gt; 1">
                        <div class="spacer">&#160;</div>
                    </xsl:if>
                </span>
            </div>
        </xsl:if>
    </xsl:template>
    <xsl:template name="itemSummaryView-DIM-googleurl">
        <xsl:if test="dim:field[@mdschema='cg' and @element='identifier' and @qualifier='googleurl' ]">
            <div class="text-left">
                <strong>
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.item-identifier-googleurl</i18n:text>
                </strong>

                <span >
                    <xsl:for-each select="dim:field[@mdschema='cg' and @element='identifier' and @qualifier='googleurl']">
                        <xsl:choose>
                            <xsl:when test="node()">
                                <a target="_blank">
                                    <xsl:attribute name="href">
                                        <xsl:copy-of select="./node()"/>
                                    </xsl:attribute>
                                    <xsl:copy-of select="./node()"/>
                                </a>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>&#160;</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:if test="count(following-sibling::dim:field[@mdschema='cg' and @element='identifier' and @qualifier='googleurl']) != 0">
                            <xsl:text>; </xsl:text>
                        </xsl:if>
                    </xsl:for-each>
                    <xsl:if test="count(dim:field[@mdschema='cg' and @element='identifier' and @qualifier='googleurl'] ) &gt; 1">
                        <div class="spacer">&#160;</div>
                    </xsl:if>
                </span>
            </div>
        </xsl:if>
    </xsl:template>
 <xsl:template name="itemSummaryView-DIM-permanenturi">
        <xsl:if test="dim:field[@element='identifier' and @qualifier='uri' ]">
            <div class="text-left">
                <strong>
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.item-identifier-permanenturi</i18n:text>
                </strong>

                <span >
                    <xsl:for-each select="dim:field[@element='identifier' and @qualifier='uri']">
                        <xsl:choose>
                            <xsl:when test="node()">
                                <a target="_blank">
                                    <xsl:attribute name="href">
                                        <xsl:copy-of select="./node()"/>
                                    </xsl:attribute>
                                    <xsl:copy-of select="./node()"/>
                                </a>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>&#160;</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:if test="count(following-sibling::dim:field[@element='identifier' and @qualifier='uri']) != 0">
                            <xsl:text>; </xsl:text>
                        </xsl:if>
                    </xsl:for-each>
                    <xsl:if test="count(dim:field[@element='identifier' and @qualifier='uri'] ) &gt; 1">
                        <div class="spacer">&#160;</div>
                    </xsl:if>
                </span>
            </div>
        </xsl:if>
    </xsl:template>
    <xsl:template name="itemSummaryView-DIM-interneturl">
        <xsl:if test="dim:field[@mdschema='cg' and @element='identifier' and @qualifier='url' ]">
            <div class="text-left">
                <strong>
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.item-identifier-interneturl</i18n:text>
                </strong>
                <span >
                    <xsl:for-each select="dim:field[@mdschema='cg' and @element='identifier' and @qualifier='url']">
                        <xsl:choose>
                            <xsl:when test="node()">
                                <a target="_blank">
                                    <xsl:attribute name="href">
                                        <xsl:copy-of select="./node()"/>
                                    </xsl:attribute>
                                    <xsl:copy-of select="./node()"/>
                                </a>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>&#160;</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:if test="count(following-sibling::dim:field[@mdschema='cg' and @element='identifier' and @qualifier='url']) != 0">
                            <xsl:text>; </xsl:text>
                        </xsl:if>
                    </xsl:for-each>
                    <xsl:if test="count(dim:field[@mdschema='cg' and @element='identifier' and @qualifier='url'] ) &gt; 1">
                        <div class="spacer">&#160;</div>
                    </xsl:if>
                </span>
            </div>
        </xsl:if>
    </xsl:template>  <xsl:template name="itemSummaryView-DIM-doi">
        <xsl:if test="dim:field[@mdschema='cg' and @element='identifier' and @qualifier='doi' ]">
            <div class="text-left">
                <strong>
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.item-identifier-doi</i18n:text>
                </strong>

                <span >
                    <xsl:for-each select="dim:field[@mdschema='cg' and @element='identifier' and @qualifier='doi']">
                        <xsl:choose>
                            <xsl:when test="node()">
                                <a target="_blank">
                                    <xsl:attribute name="href">
                                        <xsl:copy-of select="./node()"/>
                                    </xsl:attribute>
                                    <xsl:copy-of select="./node()"/>
                                </a>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>&#160;</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:if test="count(following-sibling::dim:field[@mdschema='cg' and @element='identifier' and @qualifier='doi']) != 0">
                            <xsl:text>; </xsl:text>
                        </xsl:if>
                    </xsl:for-each>
                    <xsl:if test="count(dim:field[@mdschema='cg' and @element='identifier' and @qualifier='doi'] ) &gt; 1">
                        <div class="spacer">&#160;</div>
                    </xsl:if>
                </span>
            </div>
        </xsl:if>
    </xsl:template>

    </xsl:stylesheet>
