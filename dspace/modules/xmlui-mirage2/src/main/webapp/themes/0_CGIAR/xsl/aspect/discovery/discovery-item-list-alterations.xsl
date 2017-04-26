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

        exclude-result-prefixes="xalan encoder i18n dri mets dim xlink xsl util confman url">

    <xsl:import href="../artifactbrowser/item-list-alterations.xsl"/>
    <xsl:output indent="yes"/>

    <xsl:template match="dri:reference" mode="summaryList">
        <xsl:variable name="externalMetadataURL">
            <xsl:text>cocoon:/</xsl:text>
            <xsl:value-of select="@url"/>
            <!-- Since this is a summary only grab the descriptive metadata, and the thumbnails -->
            <xsl:text>?sections=dmdSec,fileSec</xsl:text>
            <!-- An example of requesting a specific metadata standard (MODS and QDC crosswalks only work for items)->
            <xsl:if test="@type='DSpace Item'">
                <xsl:text>&amp;dmdTypes=DC</xsl:text>
            </xsl:if>-->
        </xsl:variable>
        <xsl:comment> External Metadata URL: <xsl:value-of select="$externalMetadataURL"/> </xsl:comment>
        <li>
            <xsl:attribute name="class">
                <xsl:text>ds-artifact-item </xsl:text>
                <xsl:choose>
                    <xsl:when test="position() mod 2 = 0">even</xsl:when>
                    <xsl:otherwise>odd</xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
            <xsl:apply-templates select="document($externalMetadataURL)" mode="summaryList"/>
            <xsl:apply-templates />
        </li>
    </xsl:template>
    <xsl:template name="itemSummaryList">

        <xsl:param name="handle"/>
        <xsl:param name="externalMetadataUrl"/>
        <xsl:variable name="itemWithdrawn" select="./mets:dmdSec/mets:mdWrap[@OTHERMDTYPE='DIM']/mets:xmlData/dim:dim/@withdrawn" />

        <xsl:variable name="href">
            <xsl:choose>
                <xsl:when test="$itemWithdrawn">
                    <xsl:value-of select="@OBJEDIT"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="@OBJID"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:variable name="metsDoc" select="document($externalMetadataUrl)"/>

        <div class="row ds-artifact-item ">
            <!--Generates thumbnails (if present)-->
            <div class="col-sm-3 hidden-xs">
                <xsl:apply-templates select="$metsDoc/mets:METS/mets:fileSec" mode="artifact-preview">
                    <xsl:with-param name="href" select="concat($context-path, '/handle/', $handle)"/>
                </xsl:apply-templates>
            </div>


            <div class="col-sm-9 artifact-description">
                <div class="artifact-description">

                    <div>
                        <span class="descriptionlabel">Title: </span>
                        <a class="description-info">
                            <xsl:attribute name="href">
                                <xsl:value-of select="concat($context-path, '/handle/', $handle)"/>
                            </xsl:attribute>

                            <xsl:choose>
                                <xsl:when test="dri:list[@n=(concat($handle, ':dc.title'))]">
                                    <xsl:value-of select="dri:list[@n=(concat($handle, ':dc.title'))]/dri:item"/>
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
                    <div >
                        <span class="descriptionlabel" >Authors:</span>
                        <span class="description-info">
                            <xsl:choose>
                                <xsl:when test="dri:list[@n=(concat($handle, ':dc.contributor.author'))]">
                                    <xsl:for-each select="dri:list[@n=(concat($handle, ':dc.contributor.author'))]/dri:item">
                                        <span>
                                            <xsl:if test="@authority">
                                                <xsl:attribute name="class"><xsl:text>ds-dc_contributor_author-authority</xsl:text></xsl:attribute>
                                            </xsl:if>
                                            <xsl:variable name="authorLink">
                                                <xsl:value-of select="concat($context-path,'/discover?filtertype=author&amp;filter_relational_operator=equals&amp;filter=',url:encode(node()))"></xsl:value-of>
                                            </xsl:variable>
                                            <a target="_blank">
                                                <xsl:attribute name="href" >
                                                    <xsl:value-of select="$authorLink"/>
                                                </xsl:attribute>
                                                <xsl:copy-of select="node()"/>
                                            </a>
                                        </span>
                                        <xsl:if test="count(following-sibling::dri:item) != 0">
                                            <xsl:text>; </xsl:text>
                                        </xsl:if>

                                    </xsl:for-each>
                                </xsl:when>
                                <xsl:when test="dri:list[@n=(concat($handle, ':dc.creator'))]">
                                    <xsl:for-each select="dri:list[@n=(concat($handle, ':dc.creator'))]/dri:item">
                                        <xsl:apply-templates select="."/>
                                        <xsl:if test="count(following-sibling::dri:item) != 0">
                                            <xsl:text>; </xsl:text>
                                        </xsl:if>
                                    </xsl:for-each>
                                </xsl:when>
                                <xsl:when test="dri:list[@n=(concat($handle, ':dc.contributor'))]">
                                    <xsl:for-each select="dri:list[@n=(concat($handle, ':dc.contributor'))]/dri:item">
                                        <xsl:apply-templates select="."/>
                                        <xsl:if test="count(following-sibling::dri:item) != 0">
                                            <xsl:text>; </xsl:text>
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


                        <xsl:if test="dri:list[@n=(concat($handle, ':dc.date.issued'))]">
                            <div>
                                <span class="descriptionlabel">Date:</span>

                                <span class="date">
                                    <xsl:value-of
                                            select="substring(dri:list[@n=(concat($handle, ':dc.date.issued'))]/dri:item,1,10)"/>
                                </span>

                            </div>
                        </xsl:if>
                        <xsl:if test="dri:list[@n=(concat($handle, ':dc.type'))]">
                            <xsl:variable name="type" select="dri:list[@n=(concat($handle, ':dc.type'))]/dri:item"/>
                            <div class="artifact-type">
                                <span class="descriptionlabel">Type:</span>
                                <xsl:value-of select="$type"/>
                            </div>
                        </xsl:if>
                        <xsl:if test="dri:list[@n=(concat($handle, ':cg.identifier.status'))]">
                            <xsl:variable name="status" select="dri:list[@n=(concat($handle, ':cg.identifier.status'))]/dri:item"/>
                            <div class="artifact-type">
                                <span class="descriptionlabel">Status:</span>
                                <xsl:value-of select="$status"/>
                            </div>
                        </xsl:if>
                    </div>

                </div>
            </div>
        </div>
    </xsl:template>
    <xsl:template match="dri:list/dri:list/dri:list" mode="dsoList" priority="8">
        <!--
            Retrieve the type from our name, the name contains the following format:
                {handle}:{metadata}
        -->
        <xsl:variable name="handle">
            <xsl:value-of select="substring-before(@n, ':')"/>
        </xsl:variable>
        <xsl:variable name="type">
            <xsl:value-of select="substring-after(@n, ':')"/>
        </xsl:variable>
        <xsl:variable name="externalMetadataURL">
            <xsl:text>cocoon://metadata/handle/</xsl:text>
            <xsl:value-of select="$handle"/>
            <xsl:text>/mets.xml</xsl:text>
            <!-- Since this is a summary only grab the descriptive metadata, and the thumbnails -->
            <xsl:text>?sections=dmdSec,fileSec</xsl:text>
            <!-- An example of requesting a specific metadata standard (MODS and QDC crosswalks only work for items)->
            <xsl:if test="@type='DSpace Item'">
                <xsl:text>&amp;dmdTypes=DC</xsl:text>
            </xsl:if>-->
        </xsl:variable>


        <xsl:choose>
            <xsl:when test="$type='community'">
                <xsl:call-template name="communitySummaryList">
                    <xsl:with-param name="handle">
                        <xsl:value-of select="$handle"/>
                    </xsl:with-param>
                    <xsl:with-param name="externalMetadataUrl">
                        <xsl:value-of select="$externalMetadataURL"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$type='collection'">
                <xsl:call-template name="collectionSummaryList">
                    <xsl:with-param name="handle">
                        <xsl:value-of select="$handle"/>
                    </xsl:with-param>
                    <xsl:with-param name="externalMetadataUrl">
                        <xsl:value-of select="$externalMetadataURL"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$type='item'">
                <xsl:call-template name="itemSummaryList">
                    <xsl:with-param name="handle">
                        <xsl:value-of select="$handle"/>
                    </xsl:with-param>
                    <xsl:with-param name="externalMetadataUrl">
                        <xsl:value-of select="$externalMetadataURL"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

</xsl:stylesheet>