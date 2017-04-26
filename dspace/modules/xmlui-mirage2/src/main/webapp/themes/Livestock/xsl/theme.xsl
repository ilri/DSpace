<?xml version="1.0" encoding="UTF-8"?>
    <xsl:stylesheet xmlns:i18n="http://apache.org/cocoon/i18n/2.1"
                    xmlns:dri="http://di.tamu.edu/DRI/1.0/"
                    xmlns:mets="http://www.loc.gov/METS/"
                    xmlns:xlink="http://www.w3.org/TR/xlink/"
                    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
                    xmlns:dim="http://www.dspace.org/xmlns/dspace/dim"
                    xmlns:xhtml="http://www.w3.org/1999/xhtml"
                    xmlns:mods="http://www.loc.gov/mods/v3"
                    xmlns:dc="http://purl.org/dc/elements/1.1/"
                    xmlns="http://www.w3.org/1999/xhtml"
                    exclude-result-prefixes="i18n dri mets xlink xsl dim xhtml mods dc">

    <!-- import majority of theme logic from CGIAR -->
    <xsl:import href="../../0_CGIAR/xsl/theme.xsl"/>

    <!-- Alterations for page-structure.xsl so we can use a custom Google Analytics ID in the child theme -->
    <xsl:import href="core/page-structure-alterations.xsl"/>
    <xsl:variable name="theme-google-analytics-id" select="'UA-93178643-1'"/>

    <xsl:variable name="theme-path" select="concat($context-path,'/themes/0_CGIAR/')"/>
    <xsl:output indent="yes"/>
</xsl:stylesheet>
