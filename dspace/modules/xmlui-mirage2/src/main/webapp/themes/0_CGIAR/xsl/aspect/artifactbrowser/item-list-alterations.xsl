<!--

    The contents of this file are subject to the license and copyright
    detailed in the LICENSE and NOTICE files at the root of the source
    tree and available online at

    http://www.dspace.org/license/

-->

<!--
    Rendering of a list of items (e.g. in a search or
    browse results page)

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
        xmlns:confman="org.dspace.core.ConfigurationManager"
        xmlns:url="http://whatever/java/java.net.URLEncoder"
        xmlns:fallback="org.dspace.app.xmlui.aspect.artifactbrowser.ThumbnailFallBackImagesUtil"
        exclude-result-prefixes="xalan encoder i18n dri mets dim xlink xsl util confman url fallback">

    <xsl:output indent="yes"/>


    <!--handles the rendering of a single item in a list in file mode-->
    <!--handles the rendering of a single item in a list in metadata mode-->
    <xsl:template match="dim:dim" mode="itemSummaryList-DIM-metadata">
        <xsl:param name="href"/>
        <div class="artifact-description">

            <div>
                <span class="descriptionlabel">Title:</span>
                <a class="description-info">
                    <xsl:attribute name="href">
                        <xsl:value-of select="$href"/>
                    </xsl:attribute>

                    <xsl:choose>
                        <xsl:when test="dim:field[@element='title']">
                            <xsl:value-of select="dim:field[@element='title'][1]/node()"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <i18n:text>xmlui.dri2xhtml.METS-1.0.no-title</i18n:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </a>
                <span class="Z3988">
                    <xsl:attribute name="title">
                        <xsl:call-template name="renderCOinS"/>
                    </xsl:attribute>
                    &#xFEFF; <!-- non-breaking space to force separating the end tag -->
                </span>

            </div>
            <div>
                <span class="descriptionlabel">Authors:</span>
                <span class="description-info">
                    <xsl:choose>
                        <xsl:when test="dim:field[@element='contributor'][@qualifier='author']">
                            <xsl:for-each select="dim:field[@element='contributor'][@qualifier='author']">
                                <span>
                                    <xsl:if test="@authority">
                                        <xsl:attribute name="class">
                                            <xsl:text>ds-dc_contributor_author-authority</xsl:text>
                                        </xsl:attribute>
                                    </xsl:if>
                                    <xsl:variable name="authorLink">
                                        <xsl:value-of
                                                select="concat($context-path,'/discover?filtertype=author&amp;filter_relational_operator=equals&amp;filter=',url:encode(node()))"></xsl:value-of>
                                    </xsl:variable>
                                    <a target="_blank">
                                        <xsl:attribute name="href">
                                            <xsl:value-of select="$authorLink"/>
                                        </xsl:attribute>
                                        <xsl:copy-of select="node()"/>
                                    </a>
                                </span>
                                <xsl:if test="count(following-sibling::dim:field[@element='contributor'][@qualifier='author']) != 0">
                                    <xsl:text>; </xsl:text>
                                </xsl:if>

                            </xsl:for-each>
                        </xsl:when>
                        <xsl:when test="dim:field[@element='creator']">
                            <xsl:for-each select="dim:field[@element='creator']">
                                <xsl:copy-of select="node()"/>
                                <xsl:if test="count(following-sibling::dim:field[@element='creator']) != 0">
                                    <xsl:text>, </xsl:text>
                                </xsl:if>
                            </xsl:for-each>
                        </xsl:when>
                        <xsl:when test="dim:field[@element='contributor']">
                            <xsl:for-each select="dim:field[@element='contributor']">
                                <xsl:copy-of select="node()"/>
                                <xsl:if test="count(following-sibling::dim:field[@element='contributor']) != 0">
                                    <xsl:text>, </xsl:text>
                                </xsl:if>
                            </xsl:for-each>
                        </xsl:when>
                        <xsl:otherwise>
                            <i18n:text>xmlui.dri2xhtml.METS-1.0.no-author</i18n:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </span>
            </div>
            <div>
                <xsl:if test="dim:field[@element='date' and @qualifier='issued']">
                    <div>
                        <span class="descriptionlabel">Date:</span>

                        <span class="date">
                            <xsl:value-of
                                    select="substring(dim:field[@element='date' and @qualifier='issued']/node(),1,10)"/>
                        </span>

                    </div>
                </xsl:if>
                <xsl:if test="dim:field[@element = 'type']">
                    <xsl:variable name="type" select="dim:field[@element = 'type']/node()"/>
                    <div class="artifact-type">
                        <span class="descriptionlabel">Type:</span>
                        <xsl:value-of select="$type"/>
                    </div>
                </xsl:if>
                <xsl:if test="dim:field[@mdschema='cg' and @element = 'identifier' and @qualifier='status']">
                    <xsl:variable name="status"
                                  select="dim:field[@mdschema='cg' and @element = 'identifier' and @qualifier='status']/node()"/>
                    <div class="artifact-type">
                        <span class="descriptionlabel">Status:</span>
                        <xsl:value-of select="$status"/>
                    </div>
                </xsl:if>
            </div>

        </div>
    </xsl:template>

    <xsl:template match="mets:fileSec" mode="artifact-preview">
        <xsl:param name="href"/>
        <div class="thumbnail artifact-preview">

            <a class="image-link" href="{$href}">
                <xsl:choose>
                    <!--Check if the user is allowed to see the actual thumbnail -> if not, revert to the fallback thumbnail functionality -->
                    <xsl:when test="mets:fileGrp[@USE='THUMBNAIL'] and not(contains(//mets:fileSec/mets:fileGrp[@USE='THUMBNAIL']/mets:file/mets:FLocat[@LOCTYPE='URL']/@xlink:href,'isAllowed=n'))">
                        <img class="img-responsive" alt="xmlui.mirage2.item-list.thumbnail" i18n:attr="alt">
                            <xsl:attribute name="src">
                                <xsl:value-of
                                        select="mets:fileGrp[@USE='THUMBNAIL']/mets:file/mets:FLocat[@LOCTYPE='URL']/@xlink:href"/>
                            </xsl:attribute>
                        </img>
                    </xsl:when>
                    <!-- No thumbnail available-->
                    <!-- Check what mimetype and show generic thumbnail accordingly-->
                    <xsl:otherwise>
                        <xsl:choose>
                            <xsl:when test="mets:fileGrp[@USE='CONTENT']">
                                <xsl:variable name="mimetype"
                                              select="mets:fileGrp[@USE='CONTENT']/mets:file/@MIMETYPE"/>
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

            </a>
        </div>
    </xsl:template>


</xsl:stylesheet>
