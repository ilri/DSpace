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
        xmlns:fallback="org.dspace.app.xmlui.aspect.artifactbrowser.ThumbnailFallBackImagesUtil"
        exclude-result-prefixes="xalan encoder i18n dri mets dim xlink xsl util jstring rights confman url fallback">

    <xsl:import href="item-view-DIM-helper.xsl"/>
    <xsl:output indent="yes"/>

    <xsl:template name="itemSummaryView-DIM">
        <!-- Generate the info about the item from the metadata section -->
        <xsl:apply-templates select="./mets:dmdSec/mets:mdWrap[@OTHERMDTYPE='DIM']/mets:xmlData/dim:dim"
                             mode="itemSummaryView-DIM"/>

        <xsl:copy-of select="$SFXLink" />

        <!-- Generate the Creative Commons license information from the file section (DSpace deposit license hidden by default)-->
        <xsl:if test="./mets:fileSec/mets:fileGrp[@USE='CC-LICENSE' or @USE='LICENSE']">
            <div class="license-info table">
                <p>
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.license-text</i18n:text>
                </p>
                <ul class="list-unstyled">
                    <xsl:apply-templates select="./mets:fileSec/mets:fileGrp[@USE='CC-LICENSE' or @USE='LICENSE']" mode="simple"/>
                </ul>
            </div>
        </xsl:if>


    </xsl:template>

    <!-- An item rendered in the detailView pattern, the "full item record" view of a DSpace item in Manakin. -->
    <xsl:template name="itemDetailView-DIM">
        <!-- Output all of the metadata about the item from the metadata section -->
        <xsl:apply-templates select="mets:dmdSec/mets:mdWrap[@OTHERMDTYPE='DIM']/mets:xmlData/dim:dim"
                             mode="itemDetailView-DIM"/>

        <!-- Generate the bitstream information from the file section -->
        <xsl:choose>
            <xsl:when test="./mets:fileSec/mets:fileGrp[@USE='CONTENT' or @USE='ORIGINAL' or @USE='LICENSE']/mets:file">
                <h3><i18n:text>xmlui.dri2xhtml.METS-1.0.item-files-head</i18n:text></h3>
                <div class="file-list">
                    <xsl:apply-templates select="./mets:fileSec/mets:fileGrp[@USE='CONTENT' or @USE='ORIGINAL' or @USE='LICENSE' or @USE='CC-LICENSE']">
                        <xsl:with-param name="context" select="."/>
                        <xsl:with-param name="primaryBitstream" select="./mets:structMap[@TYPE='LOGICAL']/mets:div[@TYPE='DSpace Item']/mets:fptr/@FILEID"/>
                    </xsl:apply-templates>
                </div>
            </xsl:when>
            <!-- Special case for handling ORE resource maps stored as DSpace bitstreams -->
            <xsl:when test="./mets:fileSec/mets:fileGrp[@USE='ORE']">
                <xsl:apply-templates select="./mets:fileSec/mets:fileGrp[@USE='ORE']" mode="itemDetailView-DIM" />
            </xsl:when>
            <xsl:otherwise>
                <h2><i18n:text>xmlui.dri2xhtml.METS-1.0.item-files-head</i18n:text></h2>
                <table class="ds-table file-list">
                    <tr class="ds-table-header-row">
                        <th><i18n:text>xmlui.dri2xhtml.METS-1.0.item-files-file</i18n:text></th>
                        <th><i18n:text>xmlui.dri2xhtml.METS-1.0.item-files-size</i18n:text></th>
                        <th><i18n:text>xmlui.dri2xhtml.METS-1.0.item-files-format</i18n:text></th>
                        <th><i18n:text>xmlui.dri2xhtml.METS-1.0.item-files-view</i18n:text></th>
                    </tr>
                    <tr>
                        <td colspan="4">
                            <p><i18n:text>xmlui.dri2xhtml.METS-1.0.item-no-files</i18n:text></p>
                        </td>
                    </tr>
                </table>
            </xsl:otherwise>
        </xsl:choose>

    </xsl:template>


    <xsl:template match="dim:dim" mode="itemSummaryView-DIM">
        <div class="item-summary-view-metadata">
            <xsl:call-template name="itemSummaryView-DIM-title"/>
            <div class="row">
                <div class="col-sm-4">
                    <div class="row">
                        <div class="col-xs-6 col-sm-12">
                            <xsl:call-template name="itemSummaryView-DIM-thumbnail"/>
                        </div>
                        <div class="col-xs-6 col-sm-12">
                            <xsl:call-template name="itemSummaryView-DIM-file-section"/>
                        </div>
                     </div>

                    <xsl:call-template name="itemSummaryView-DIM-authors"/>
                    <xsl:call-template name="itemSummaryView-DIM-date"/>
                    <xsl:call-template name="itemSummaryView-DIM-language"/>
                    <xsl:call-template name="itemSummaryView-DIM-type"/>
                    <xsl:call-template name="itemSummaryView-DIM-review-status"/>
                    <xsl:call-template name="itemSummaryView-DIM-isijournal"/>
                    <xsl:call-template name="itemSummaryView-DIM-accessibility"/>
                    <xsl:call-template name="itemSummaryView-DIM-usage-rights"/>


                    <xsl:if test="$ds_item_view_toggle_url != ''">
                        <xsl:call-template name="itemSummaryView-show-full"/>
                    </xsl:if>

                </div>
                <div class="col-sm-8">
                    <!-- set the row to flex and vertically align items -->
                    <div class="row" style="display: flex; align-items: center;">
                        <div class="col-sm-4">
                            <xsl:if test="dim:field[@element='identifier' and @qualifier='uri']">
                                <xsl:call-template name='itemSummaryView-sharing'/>
                            </xsl:if>
                        </div>

                        <xsl:if test="confman:getProperty('altmetric.enabled') and ($identifier_doi or $identifier_handle)">
                        <!-- center align the Altmetric badge (PNG file) -->
                        <div class="col-sm-4" style="text-align: center;">
                            <xsl:call-template name='impact-altmetric'/>
                        </div>
                        </xsl:if>

                        <xsl:if test="$identifier_doi">
                        <!-- dimensions badge is an SVG and needs to be centered
                             a different way, but anyways it looks better if we
                             don't center it... for now -->
                        <div class="col-sm-4">
                            <xsl:call-template name='impact-dimensions'/>
                        </div>
                        </xsl:if>
                    </div>

                    <xsl:call-template name="itemSummaryView-DIM-citation"/>
                    <xsl:call-template name="itemSummaryView-DIM-identifiers"/>
                    <xsl:call-template name="itemSummaryView-DIM-abstract"/>
                    <xsl:call-template name="itemSummaryView-DIM-orcids"/>
                    <xsl:call-template name="itemSummaryView-DIM-notes"/>
                    <xsl:call-template name="itemSummaryView-DIM-affiliations"/>
                    <xsl:call-template name="itemSummaryView-DIM-subject"/>
                    <xsl:call-template name="itemSummaryView-DIM-subjects"/>
                    <xsl:call-template name="itemSummaryView-DIM-countries"/>
                    <xsl:call-template name="itemSummaryView-DIM-regions"/>
                    <xsl:call-template name="itemSummaryView-DIM-species"/>
                    <xsl:call-template name="itemSummaryView-DIM-breeds"/>
                    <xsl:call-template name="itemSummaryView-DIM-investors-sponsors"/>
                    <xsl:call-template name="itemSummaryView-DIM-related-material"/>

                    <div class="simple-item-view-collections item-page-field-wrapper table">
                        <xsl:call-template name="itemSummaryView-collections"/>
                    </div>
                </div>
            </div>
        </div>
    </xsl:template>

    <xsl:template name="itemSummaryView-DIM-title">
        <xsl:choose>
            <xsl:when test="count(dim:field[@element='title'][not(@qualifier)]) &gt; 1">
                <h2 class="page-header first-page-header">
                    <xsl:value-of select="dim:field[@element='title'][not(@qualifier)][1]/node()"/>
                </h2>
                <div class="simple-item-view-other">
                    <p class="lead">
                        <xsl:for-each select="dim:field[@element='title'][not(@qualifier)]">
                            <xsl:if test="not(position() = 1)">
                                <xsl:value-of select="./node()"/>
                                <xsl:if test="count(following-sibling::dim:field[@element='title'][not(@qualifier)]) != 0">
                                    <xsl:text>; </xsl:text>
                                    <br/>
                                </xsl:if>
                            </xsl:if>

                        </xsl:for-each>
                    </p>
                </div>
            </xsl:when>
            <xsl:when test="count(dim:field[@element='title'][not(@qualifier)]) = 1">
                <h2 class="page-header first-page-header">
                    <xsl:value-of select="dim:field[@element='title'][not(@qualifier)][1]/node()"/>
                </h2>
            </xsl:when>
            <xsl:otherwise>
                <h2 class="page-header first-page-header">
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.no-title</i18n:text>
                </h2>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="itemSummaryView-DIM-thumbnail">
        <div class="thumbnail">
            <xsl:choose>
                <!-- Alan: check if there is a thumbnail and that the link is allowed -->
                <xsl:when test="//mets:fileSec/mets:fileGrp[@USE='THUMBNAIL'] and not(contains(//mets:fileSec/mets:fileGrp[@USE='THUMBNAIL']/mets:file/mets:FLocat[@LOCTYPE='URL']/@xlink:href,'isAllowed=n'))">
                    <!-- Alan: start determining the value of the src variable -->
                    <xsl:variable name="src">
                        <xsl:choose>
                            <!-- Alan: check if groupid for thumbnail is the same as that of the first content bitstream -->
                            <xsl:when test="/mets:METS/mets:fileSec/mets:fileGrp[@USE='THUMBNAIL']/mets:file[@GROUPID=../../mets:fileGrp[@USE='CONTENT']/mets:file[@GROUPID=../../mets:fileGrp[@USE='THUMBNAIL']/mets:file/@GROUPID][1]/@GROUPID]">
                                <!-- Alan: select the URL of the thumbnail -->
                                <xsl:value-of
                                        select="/mets:METS/mets:fileSec/mets:fileGrp[@USE='THUMBNAIL']/mets:file[@GROUPID=../../mets:fileGrp[@USE='CONTENT']/mets:file[@GROUPID=../../mets:fileGrp[@USE='THUMBNAIL']/mets:file/@GROUPID][1]/@GROUPID]/mets:FLocat[@LOCTYPE='URL']/@xlink:href"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of
                                        select="//mets:fileSec/mets:fileGrp[@USE='THUMBNAIL']/mets:file/mets:FLocat[@LOCTYPE='URL']/@xlink:href"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:variable>
                    <!-- Alan: if there is a content bitstream, add a link to the thumbnail -->
                    <xsl:choose>
                        <xsl:when test="//mets:fileSec/mets:fileGrp[@USE='CONTENT']/mets:file/mets:FLocat[@LOCTYPE='URL']/@xlink:href">
                            <a>
                                <xsl:attribute name="href">
                                    <xsl:value-of select="//mets:fileSec/mets:fileGrp[@USE='CONTENT']/mets:file/mets:FLocat[@LOCTYPE='URL']/@xlink:href"/>
                                </xsl:attribute>

                                <img alt="Thumbnail">
                                    <xsl:attribute name="src">
                                        <xsl:value-of select="$src"/>
                                    </xsl:attribute>
                                </img>
                            </a>
                        </xsl:when>
                        <!-- Alan: otherwise, just print the thumbnail -->
                        <xsl:otherwise>

                            <img alt="Thumbnail">
                                <xsl:attribute name="src">
                                    <xsl:value-of select="$src"/>
                                </xsl:attribute>
                            </img>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:choose>
                        <xsl:when test="//mets:fileGrp[@USE='CONTENT']">
                            <xsl:variable name="mimetype"
                                          select="//mets:fileGrp[@USE='CONTENT']/mets:file/@MIMETYPE"/>
                            <xsl:variable name="fallbackImage">
                                <xsl:value-of select="fallback:getFallBackImagesAssociatedToExtension($mimetype)"/>
                            </xsl:variable>
                            <img alt="xmlui.mirage2.item-list.thumbnail" i18n:attr="alt"
                                 src="{concat($theme-path, $fallbackImage)}"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:variable name="fallbackImage">
                                <xsl:value-of select="fallback:getFallBackImagesAssociatedToExtension('default')"/>
                            </xsl:variable>
                            <img alt="xmlui.mirage2.item-list.thumbnail" i18n:attr="alt"
                                 src="{concat($theme-path, $fallbackImage)}"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:otherwise>
            </xsl:choose>
        </div>
    </xsl:template>



<xsl:template name="itemSummaryView-collections">
<xsl:if test="$document//dri:referenceSet[@id='aspect.artifactbrowser.ItemViewer.referenceSet.collection-viewer']">
    <div class="simple-item-view-collections item-page-field-wrapper table">
        <h5 class="bold">
            <i18n:text>xmlui.mirage2.itemSummaryView.Collections</i18n:text>
        </h5>
        <xsl:apply-templates select="$document//dri:referenceSet[@id='aspect.artifactbrowser.ItemViewer.referenceSet.collection-viewer']/dri:reference"/>
    </div>
</xsl:if>
</xsl:template>

<xsl:template name="itemSummaryView-DIM-file-section">
<xsl:choose>
    <xsl:when test="//mets:fileSec/mets:fileGrp[@USE='CONTENT' or @USE='ORIGINAL' or @USE='LICENSE']/mets:file">
        <div class="item-page-field-wrapper table">
            <h5 class="bold">
                <i18n:text>xmlui.dri2xhtml.METS-1.0.item-files-viewOpen</i18n:text>
            </h5>

            <xsl:variable name="label-1">
                <xsl:choose>
                    <xsl:when test="confman:getProperty('mirage2.item-view.bitstream.href.label.1')">
                        <xsl:value-of select="confman:getProperty('mirage2.item-view.bitstream.href.label.1')"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>label</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="label-2">
                <xsl:choose>
                    <xsl:when test="confman:getProperty('mirage2.item-view.bitstream.href.label.2')">
                        <xsl:value-of select="confman:getProperty('mirage2.item-view.bitstream.href.label.2')"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>title</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:for-each select="//mets:fileSec/mets:fileGrp[@USE='CONTENT' or @USE='ORIGINAL' or @USE='LICENSE']/mets:file">
                <xsl:call-template name="itemSummaryView-DIM-file-section-entry">
                    <xsl:with-param name="href" select="mets:FLocat[@LOCTYPE='URL']/@xlink:href" />
                    <xsl:with-param name="mimetype" select="@MIMETYPE" />
                    <xsl:with-param name="label-1" select="$label-1" />
                    <xsl:with-param name="label-2" select="$label-2" />
                    <xsl:with-param name="title" select="mets:FLocat[@LOCTYPE='URL']/@xlink:title" />
                    <xsl:with-param name="label" select="mets:FLocat[@LOCTYPE='URL']/@xlink:label" />
                    <xsl:with-param name="size" select="@SIZE" />
                </xsl:call-template>
            </xsl:for-each>
        </div>
    </xsl:when>
    <!-- Special case for handling ORE resource maps stored as DSpace bitstreams -->
            <xsl:when test="//mets:fileSec/mets:fileGrp[@USE='ORE']">
                <xsl:apply-templates select="//mets:fileSec/mets:fileGrp[@USE='ORE']" mode="itemSummaryView-DIM" />
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="itemSummaryView-DIM-file-section-entry">
        <xsl:param name="href" />
        <xsl:param name="mimetype" />
        <xsl:param name="label-1" />
        <xsl:param name="label-2" />
        <xsl:param name="title" />
        <xsl:param name="label" />
        <xsl:param name="size" />
        <div>
            <a>
                <xsl:attribute name="href">
                    <xsl:value-of select="$href"/>
                </xsl:attribute>
                <xsl:call-template name="getFileIcon">
                    <xsl:with-param name="mimetype">
                        <xsl:value-of select="substring-before($mimetype,'/')"/>
                        <xsl:text>/</xsl:text>
                        <xsl:value-of select="substring-after($mimetype,'/')"/>
                    </xsl:with-param>
                </xsl:call-template>
                <xsl:choose>
                    <xsl:when test="contains($label-1, 'label') and string-length($label)!=0">
                        <xsl:value-of select="$label"/>
                    </xsl:when>
                    <xsl:when test="contains($label-1, 'title') and string-length($title)!=0">
                        <xsl:value-of select="$title"/>
                    </xsl:when>
                    <xsl:when test="contains($label-2, 'label') and string-length($label)!=0">
                        <xsl:value-of select="$label"/>
                    </xsl:when>
                    <xsl:when test="contains($label-2, 'title') and string-length($title)!=0">
                        <xsl:value-of select="$title"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="getFileTypeDesc">
                            <xsl:with-param name="mimetype">
                                <xsl:value-of select="substring-before($mimetype,'/')"/>
                                <xsl:text>/</xsl:text>
                                <xsl:choose>
                                    <xsl:when test="contains($mimetype,';')">
                                        <xsl:value-of select="substring-before(substring-after($mimetype,'/'),';')"/>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:value-of select="substring-after($mimetype,'/')"/>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:text> (</xsl:text>
                <xsl:choose>
                    <xsl:when test="$size &lt; 1024">
                        <xsl:value-of select="$size"/>
                        <i18n:text>xmlui.dri2xhtml.METS-1.0.size-bytes</i18n:text>
                    </xsl:when>
                    <xsl:when test="$size &lt; 1024 * 1024">
                        <xsl:value-of select="substring(string($size div 1024),1,5)"/>
                        <i18n:text>xmlui.dri2xhtml.METS-1.0.size-kilobytes</i18n:text>
                    </xsl:when>
                    <xsl:when test="$size &lt; 1024 * 1024 * 1024">
                        <xsl:value-of select="substring(string($size div (1024 * 1024)),1,5)"/>
                        <i18n:text>xmlui.dri2xhtml.METS-1.0.size-megabytes</i18n:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="substring(string($size div (1024 * 1024 * 1024)),1,5)"/>
                        <i18n:text>xmlui.dri2xhtml.METS-1.0.size-gigabytes</i18n:text>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:text>)</xsl:text>
            </a>
        </div>
    </xsl:template>

    <xsl:template match="dim:dim" mode="itemDetailView-DIM">
        <xsl:call-template name="itemSummaryView-DIM-title"/>
        <div class="ds-table-responsive">
            <table class="ds-includeSet-table detailtable table table-striped table-hover">
                <xsl:apply-templates mode="itemDetailView-DIM"/>
            </table>
        </div>

        <span class="Z3988">
            <xsl:attribute name="title">
                <xsl:call-template name="renderCOinS"/>
            </xsl:attribute>
            &#xFEFF; <!-- non-breaking space to force separating the end tag -->
        </span>
        <xsl:copy-of select="$SFXLink" />
    </xsl:template>

    <xsl:template match="dim:field" mode="itemDetailView-DIM">
        <tr>
            <xsl:attribute name="class">
                <xsl:text>ds-table-row </xsl:text>
                <xsl:if test="(position() div 2 mod 2 = 0)">even </xsl:if>
                <xsl:if test="(position() div 2 mod 2 = 1)">odd </xsl:if>
            </xsl:attribute>
            <td class="label-cell">
                <xsl:value-of select="./@mdschema"/>
                <xsl:text>.</xsl:text>
                <xsl:value-of select="./@element"/>
                <xsl:if test="./@qualifier">
                    <xsl:text>.</xsl:text>
                    <xsl:value-of select="./@qualifier"/>
                </xsl:if>
            </td>
            <td class="word-break">
                <xsl:copy-of select="./node()"/>
            </td>
            <td><xsl:value-of select="./@language"/></td>
        </tr>
    </xsl:template>

    <!-- don't render the item-view-toggle automatically in the summary view, only when it gets called -->
    <xsl:template match="dri:p[contains(@rend , 'item-view-toggle') and
        (preceding-sibling::dri:referenceSet[@type = 'summaryView'] or following-sibling::dri:referenceSet[@type = 'summaryView'])]">
    </xsl:template>

    <!-- don't render the head on the item view page -->
    <xsl:template match="dri:div[@n='item-view']/dri:head" priority="5">
    </xsl:template>

    <xsl:template match="mets:fileGrp[@USE='CONTENT']">
        <xsl:param name="context"/>
        <xsl:param name="primaryBitstream" select="-1"/>
        <xsl:choose>
            <!-- If one exists and it's of text/html MIME type, only display the primary bitstream -->
            <xsl:when test="mets:file[@ID=$primaryBitstream]/@MIMETYPE='text/html'">
                <xsl:apply-templates select="mets:file[@ID=$primaryBitstream]">
                    <xsl:with-param name="context" select="$context"/>
                </xsl:apply-templates>
            </xsl:when>
            <!-- Otherwise, iterate over and display all of them -->
            <xsl:otherwise>
                <xsl:apply-templates select="mets:file">
                    <!--Do not sort any more bitstream order can be changed-->
                    <xsl:with-param name="context" select="$context"/>
                </xsl:apply-templates>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="mets:fileGrp[@USE='LICENSE']">
        <xsl:param name="context"/>
        <xsl:param name="primaryBitstream" select="-1"/>
        <xsl:apply-templates select="mets:file">
            <xsl:with-param name="context" select="$context"/>
        </xsl:apply-templates>
    </xsl:template>

    <xsl:template match="mets:file">
        <xsl:param name="context" select="."/>
        <div class="file-wrapper row">
            <div class="col-xs-6 col-sm-3">
                <div class="thumbnail">
                    <a class="image-link">
                        <xsl:attribute name="href">
                            <xsl:value-of select="mets:FLocat[@LOCTYPE='URL']/@xlink:href"/>
                        </xsl:attribute>
                        <xsl:choose>
                            <xsl:when test="$context/mets:fileSec/mets:fileGrp[@USE='THUMBNAIL']/
                        mets:file[@GROUPID=current()/@GROUPID]">
                                <img alt="Thumbnail">
                                    <xsl:attribute name="src">
                                        <xsl:value-of select="$context/mets:fileSec/mets:fileGrp[@USE='THUMBNAIL']/
                                    mets:file[@GROUPID=current()/@GROUPID]/mets:FLocat[@LOCTYPE='URL']/@xlink:href"/>
                                    </xsl:attribute>
                                </img>
                            </xsl:when>
                            <xsl:otherwise>
                                <img alt="Thumbnail">
                                    <xsl:attribute name="data-src">
                                        <xsl:text>holder.js/100%x</xsl:text>
                                        <xsl:value-of select="$thumbnail.maxheight"/>
                                        <xsl:text>/text:No Thumbnail</xsl:text>
                                    </xsl:attribute>
                                </img>
                            </xsl:otherwise>
                        </xsl:choose>
                    </a>
                </div>
            </div>

            <div class="col-xs-6 col-sm-7">
                <dl class="file-metadata dl-horizontal">
                    <dt>
                        <i18n:text>xmlui.dri2xhtml.METS-1.0.item-files-name</i18n:text>
                        <xsl:text>:</xsl:text>
                    </dt>
                    <dd class="word-break">
                        <xsl:attribute name="title">
                            <xsl:value-of select="mets:FLocat[@LOCTYPE='URL']/@xlink:title"/>
                        </xsl:attribute>
                        <xsl:value-of select="util:shortenString(mets:FLocat[@LOCTYPE='URL']/@xlink:title, 30, 5)"/>
                    </dd>
                    <!-- File size always comes in bytes and thus needs conversion -->
                    <dt>
                        <i18n:text>xmlui.dri2xhtml.METS-1.0.item-files-size</i18n:text>
                        <xsl:text>:</xsl:text>
                    </dt>
                    <dd class="word-break">
                        <xsl:choose>
                            <xsl:when test="@SIZE &lt; 1024">
                                <xsl:value-of select="@SIZE"/>
                                <i18n:text>xmlui.dri2xhtml.METS-1.0.size-bytes</i18n:text>
                            </xsl:when>
                            <xsl:when test="@SIZE &lt; 1024 * 1024">
                                <xsl:value-of select="substring(string(@SIZE div 1024),1,5)"/>
                                <i18n:text>xmlui.dri2xhtml.METS-1.0.size-kilobytes</i18n:text>
                            </xsl:when>
                            <xsl:when test="@SIZE &lt; 1024 * 1024 * 1024">
                                <xsl:value-of select="substring(string(@SIZE div (1024 * 1024)),1,5)"/>
                                <i18n:text>xmlui.dri2xhtml.METS-1.0.size-megabytes</i18n:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="substring(string(@SIZE div (1024 * 1024 * 1024)),1,5)"/>
                                <i18n:text>xmlui.dri2xhtml.METS-1.0.size-gigabytes</i18n:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </dd>
                    <!-- Lookup File Type description in local messages.xml based on MIME Type.
             In the original DSpace, this would get resolved to an application via
             the Bitstream Registry, but we are constrained by the capabilities of METS
             and can't really pass that info through. -->
                    <dt>
                        <i18n:text>xmlui.dri2xhtml.METS-1.0.item-files-format</i18n:text>
                        <xsl:text>:</xsl:text>
                    </dt>
                    <dd class="word-break">
                        <xsl:call-template name="getFileTypeDesc">
                            <xsl:with-param name="mimetype">
                                <xsl:value-of select="substring-before(@MIMETYPE,'/')"/>
                                <xsl:text>/</xsl:text>
                                <xsl:choose>
                                    <xsl:when test="contains(@MIMETYPE,';')">
                                        <xsl:value-of select="substring-before(substring-after(@MIMETYPE,'/'),';')"/>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:value-of select="substring-after(@MIMETYPE,'/')"/>
                                    </xsl:otherwise>
                                </xsl:choose>

                            </xsl:with-param>
                        </xsl:call-template>
                    </dd>
                    <!-- Display the contents of 'Description' only if bitstream contains a description -->
                    <xsl:if test="mets:FLocat[@LOCTYPE='URL']/@xlink:label != ''">
                        <dt>
                            <i18n:text>xmlui.dri2xhtml.METS-1.0.item-files-description</i18n:text>
                            <xsl:text>:</xsl:text>
                        </dt>
                        <dd class="word-break">
                            <xsl:attribute name="title">
                                <xsl:value-of select="mets:FLocat[@LOCTYPE='URL']/@xlink:label"/>
                            </xsl:attribute>
                            <xsl:value-of select="util:shortenString(mets:FLocat[@LOCTYPE='URL']/@xlink:label, 30, 5)"/>
                        </dd>
                    </xsl:if>
                </dl>
            </div>

            <div class="file-link col-xs-6 col-xs-offset-6 col-sm-2 col-sm-offset-0">
                <xsl:choose>
                    <xsl:when test="@ADMID">
                        <xsl:call-template name="display-rights"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="view-open"/>
                    </xsl:otherwise>
                </xsl:choose>
            </div>
        </div>

    </xsl:template>

    <xsl:template name="view-open">
        <a>
            <xsl:attribute name="href">
                <xsl:value-of select="mets:FLocat[@LOCTYPE='URL']/@xlink:href"/>
            </xsl:attribute>
            <i18n:text>xmlui.dri2xhtml.METS-1.0.item-files-viewOpen</i18n:text>
        </a>
    </xsl:template>

    <xsl:template name="display-rights">
        <xsl:variable name="file_id" select="jstring:replaceAll(jstring:replaceAll(string(@ADMID), '_METSRIGHTS', ''), 'rightsMD_', '')"/>
        <xsl:variable name="rights_declaration" select="../../../mets:amdSec/mets:rightsMD[@ID = concat('rightsMD_', $file_id, '_METSRIGHTS')]/mets:mdWrap/mets:xmlData/rights:RightsDeclarationMD"/>
        <xsl:variable name="rights_context" select="$rights_declaration/rights:Context"/>
        <xsl:variable name="users">
            <xsl:for-each select="$rights_declaration/*">
                <xsl:value-of select="rights:UserName"/>
                <xsl:choose>
                    <xsl:when test="rights:UserName/@USERTYPE = 'GROUP'">
                        <xsl:text> (group)</xsl:text>
                    </xsl:when>
                    <xsl:when test="rights:UserName/@USERTYPE = 'INDIVIDUAL'">
                        <xsl:text> (individual)</xsl:text>
                    </xsl:when>
                </xsl:choose>
                <xsl:if test="position() != last()">, </xsl:if>
            </xsl:for-each>
        </xsl:variable>

        <xsl:choose>
            <xsl:when test="not ($rights_context/@CONTEXTCLASS = 'GENERAL PUBLIC') and ($rights_context/rights:Permissions/@DISPLAY = 'true')">
                <a href="{mets:FLocat[@LOCTYPE='URL']/@xlink:href}">
                    <img width="64" height="64" src="{concat($theme-path,'/images/Crystal_Clear_action_lock3_64px.png')}" title="Read access available for {$users}"/>
                    <!-- icon source: http://commons.wikimedia.org/wiki/File:Crystal_Clear_action_lock3.png -->
                </a>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="view-open"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="getFileIcon">
        <xsl:param name="mimetype"/>
        <i aria-hidden="true">
            <xsl:attribute name="class">
                <xsl:text>glyphicon </xsl:text>
                <xsl:choose>
                    <xsl:when test="contains(mets:FLocat[@LOCTYPE='URL']/@xlink:href,'isAllowed=n')">
                        <xsl:text> glyphicon-lock</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text> glyphicon-file</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
        </i>
        <xsl:text> </xsl:text>
    </xsl:template>

    <!-- Generate the license information from the file section -->
    <xsl:template match="mets:fileGrp[@USE='CC-LICENSE']" mode="simple">
        <li><a href="{mets:file/mets:FLocat[@xlink:title='license_text']/@xlink:href}"><i18n:text>xmlui.dri2xhtml.structural.link_cc</i18n:text></a></li>
    </xsl:template>

    <!-- Generate the license information from the file section -->
    <xsl:template match="mets:fileGrp[@USE='LICENSE']" mode="simple">
        <li><a href="{mets:file/mets:FLocat[@xlink:title='license.txt']/@xlink:href}"><i18n:text>xmlui.dri2xhtml.structural.link_original_license</i18n:text></a></li>
    </xsl:template>

    <!--
    File Type Mapping template

    This maps format MIME Types to human friendly File Type descriptions.
    Essentially, it looks for a corresponding 'key' in your messages.xml of this
    format: xmlui.dri2xhtml.mimetype.{MIME Type}

    (e.g.) <message key="xmlui.dri2xhtml.mimetype.application/pdf">PDF</message>

    If a key is found, the translated value is displayed as the File Type (e.g. PDF)
    If a key is NOT found, the MIME Type is displayed by default (e.g. application/pdf)
    -->
    <xsl:template name="getFileTypeDesc">
        <xsl:param name="mimetype"/>

        <!--Build full key name for MIME type (format: xmlui.dri2xhtml.mimetype.{MIME type})-->
        <xsl:variable name="mimetype-key">xmlui.dri2xhtml.mimetype.<xsl:value-of select='$mimetype'/></xsl:variable>

        <!--Lookup the MIME Type's key in messages.xml language file.  If not found, just display MIME Type-->
        <i18n:text i18n:key="{$mimetype-key}"><xsl:value-of select="$mimetype"/></i18n:text>
    </xsl:template>


    <xsl:template name='impact-altmetric'>
        <div id='impact-altmetric'>

            <!-- Altmetric.com -->
            <script type="text/javascript" src="{concat($scheme, 'd1bxh8uas1mnw7.cloudfront.net/assets/embed.js')}">&#160;</script>
            <div id='altmetric'
                 data-hide-no-mentions="true"
                 class='altmetric-embed'>
                <xsl:variable name='badge_type' select='confman:getProperty("altmetric.badgeType")'/>
                <xsl:if test='boolean($badge_type)'>
                    <xsl:attribute name='data-badge-type'><xsl:value-of select='$badge_type'/></xsl:attribute>
                </xsl:if>

                <xsl:variable name='badge_popover' select='confman:getProperty("altmetric.popover")'/>
                <xsl:if test='$badge_popover'>
                    <xsl:attribute name='data-badge-popover'><xsl:value-of select='$badge_popover'/></xsl:attribute>
                </xsl:if>

                <xsl:variable name='badge_details' select='confman:getProperty("altmetric.details")'/>
                <xsl:if test='$badge_details'>
                    <xsl:attribute name='data-badge-details'><xsl:value-of select='$badge_details'/></xsl:attribute>
                </xsl:if>

                <xsl:variable name='no_score' select='confman:getProperty("altmetric.noScore")'/>
                <xsl:if test='$no_score'>
                    <xsl:attribute name='data-no-score'><xsl:value-of select='$no_score'/></xsl:attribute>
                </xsl:if>

                <xsl:if test='confman:getProperty("altmetric.hideNoMentions")'>
                    <xsl:attribute name='data-hide-no-mentions'>true</xsl:attribute>
                </xsl:if>

                <xsl:variable name='link_target' select='confman:getProperty("altmetric.linkTarget")'/>
                <xsl:if test='$link_target'>
                    <xsl:attribute name='data-link-target'><xsl:value-of select='$link_target'/></xsl:attribute>
                </xsl:if>

                <xsl:choose>    <!-- data-doi data-handle data-arxiv-id data-pmid -->
                    <xsl:when test='$identifier_doi'>
                        <xsl:attribute name='data-doi'><xsl:value-of select='$identifier_doi'/></xsl:attribute>
                    </xsl:when>
                    <xsl:when test='$identifier_handle'>
                        <xsl:attribute name='data-handle'><xsl:value-of select='$identifier_handle'/></xsl:attribute>
                    </xsl:when>
                </xsl:choose>
                &#xFEFF;
            </div>
        </div>
    </xsl:template>

    <xsl:template name='impact-dimensions'>
        <div id='impact-dimensions'>
            <xsl:variable name="doi">
                <!-- extract the DOI portion of the URI -->
                <xsl:choose>
                    <xsl:when test="contains($identifier_doi, 'https://doi.org/')">
                        <xsl:call-template name="replace-string">
                            <xsl:with-param name="text" select="$identifier_doi"/>
                            <xsl:with-param name="replace" select="'https://doi.org/'" />
                            <xsl:with-param name="with" select="''"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:when test="contains($identifier_doi, 'https://dx.doi.org/')">
                        <xsl:call-template name="replace-string">
                            <xsl:with-param name="text" select="$identifier_doi"/>
                            <xsl:with-param name="replace" select="'https://dx.doi.org/'" />
                            <xsl:with-param name="with" select="''"/>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:when test="contains($identifier_doi, 'http://dx.doi.org/')">
                        <xsl:call-template name="replace-string">
                            <xsl:with-param name="text" select="$identifier_doi"/>
                            <xsl:with-param name="replace" select="'http://dx.doi.org/'" />
                            <xsl:with-param name="with" select="''"/>
                        </xsl:call-template>
                    </xsl:when>
                </xsl:choose>
            </xsl:variable>
            <!-- badge.dimensions.ai -->
            <span class="__dimensions_badge_embed__" data-hide-zero-citations="true" data-style="small_circle">
                <xsl:attribute name='data-doi'><xsl:value-of select="$doi"/></xsl:attribute>
            </span>
            <script async="true" src="https://badge.dimensions.ai/badge.js" charset="utf-8"></script>
        </div>
    </xsl:template>

</xsl:stylesheet>
