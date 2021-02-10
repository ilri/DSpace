<xsl:stylesheet xmlns:i18n="http://apache.org/cocoon/i18n/2.1"
                xmlns:dri="http://di.tamu.edu/DRI/1.0/"
                xmlns:mets="http://www.loc.gov/METS/"
                xmlns:xlink="http://www.w3.org/TR/xlink/"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
                xmlns:dim="http://www.dspace.org/xmlns/dspace/dim"
                xmlns:xhtml="http://www.w3.org/1999/xhtml"
                xmlns:mods="http://www.loc.gov/mods/v3"
                xmlns:dc="http://purl.org/dc/elements/1.1/"
                xmlns:confman="org.dspace.core.ConfigurationManager"
                exclude-result-prefixes="i18n dri mets xlink xsl dim xhtml mods dc confman">

    <xsl:output method="xml" encoding="UTF-8" indent="yes"/>

    <!-- Add a google analytics script if the key is present -->
    <xsl:template name="googleAnalytics">
        <xsl:if test="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='google'][@qualifier='analytics']">
            <script><xsl:text>
                Haven.create({
                    notification: {
                        policyUrl: "/page/privacy"
                    },
                    translations: {
                        en: {
                            notification: {
                                policy: "Our privacy statement.",
                                message: "This site uses cookies. By clicking \"agree\" and continuing to use this site you agree to our use of cookies.",
                                accept: "Agree",
                                decline: "Disagree",
                            }
                        },
                    },
                    services: [
                        {
                            name: 'google-analytics',
                            purposes: ['analytics'],
                            type: 'google-analytics',
                            inject: true,
                            options: {
                                id: '</xsl:text><xsl:value-of select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='google'][@qualifier='analytics']"/><xsl:text>',
                            }
                        }
                    ]
                });
            </xsl:text></script>
        </xsl:if>
    </xsl:template>

    <!-- Add a favicons, from https://realfavicongenerator.net -->
    <xsl:template name="favicons">
		<link rel="shortcut icon">
			<xsl:attribute name="href">
				<xsl:value-of select="$theme-path"/>
				<xsl:text>images/favicon.ico</xsl:text>
			</xsl:attribute>
		</link>
		<link rel="apple-touch-icon" sizes="180x180">
			<xsl:attribute name="href">
				<xsl:value-of select="$theme-path"/>
				<xsl:text>images/apple-touch-icon.png</xsl:text>
			</xsl:attribute>
		</link>
		<link rel="icon" type="image/png" sizes="32x32">
			<xsl:attribute name="href">
				<xsl:value-of select="$theme-path"/>
				<xsl:text>images/favicon-32x32.png</xsl:text>
			</xsl:attribute>
		</link>
		<link rel="icon" type="image/png" sizes="16x16">
			<xsl:attribute name="href">
				<xsl:value-of select="$theme-path"/>
				<xsl:text>images/favicon-16x16.png</xsl:text>
			</xsl:attribute>
		</link>
		<link rel="manifest">
			<xsl:attribute name="href">
				<xsl:value-of select="$theme-path"/>
				<xsl:text>images/site.webmanifest</xsl:text>
			</xsl:attribute>
		</link>
		<link rel="mask-icon" color="#682622">
			<xsl:attribute name="href">
				<xsl:value-of select="$theme-path"/>
				<xsl:text>images/safari-pinned-tab.svg</xsl:text>
			</xsl:attribute>
		</link>
        <meta name="msapplication-TileColor" content="#00aba9"/>
		<meta name="msapplication-config">
			<xsl:attribute name="href">
				<xsl:value-of select="$theme-path"/>
				<xsl:text>images/browserconfig.xml</xsl:text>
			</xsl:attribute>
		</meta>
        <meta name="theme-color" content="#ffffff"/>
    </xsl:template>

</xsl:stylesheet>
