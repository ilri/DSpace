<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet 
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:doc="http://www.lyncode.com/xoai"
	version="1.0">
	<xsl:output omit-xml-declaration="yes" method="xml" indent="yes" />
	
	<xsl:template match="/">
		<mods xmlns="http://www.loc.gov/mods/v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="3.7" xsi:schemaLocation="http://www.loc.gov/mods/v3 http://www.loc.gov/standards/mods/v3/mods-3-7.xsd">
			<xsl:for-each select="doc:metadata/doc:element[@name='dc']/doc:element[@name='contributor']/doc:element[@name='author']/doc:element/doc:field[@name='value']">
				<name type="personal">
					<role>
						<!-- See: https://www.loc.gov/marc/relators/relaterm.html -->
						<roleTerm type="text" authority="marcrelator">Author</roleTerm>
						<roleTerm type="code" authority="marcrelator">aut</roleTerm>
					</role>

					<namePart><xsl:value-of select="."/></namePart>
				</name>
			</xsl:for-each>

			<xsl:for-each select="doc:metadata/doc:element[@name='cg']/doc:element[@name='contributor']/doc:element[@name='donor']/doc:element/doc:field[@name='value']">
				<name type="corporate">
					<role>
						<roleTerm type="text" authority="marcrelator">Funder</roleTerm>
						<roleTerm type="code" authority="marcrelator">fnd</roleTerm>
					</role>

					<namePart><xsl:value-of select="."/></namePart>
				</name>
			</xsl:for-each>

                        <!-- See: https://www.loc.gov/standards/mods/userguide/origininfo.html -->
			<xsl:if test="doc:metadata/doc:element[@name='dcterms']/doc:element[@name='issued']/doc:element/doc:field[@name='value']">
				<originInfo eventType="publication">
					<xsl:if test="doc:metadata/doc:element[@name='cg']/doc:element[@name='place']/doc:element/doc:field[@name='value']">
						<place>
							<placeTerm type="text">
								<xsl:value-of select="doc:metadata/doc:element[@name='cg']/doc:element[@name='place']/doc:element/doc:field[@name='value']/text()"></xsl:value-of>
							</placeTerm>
						</place>
					</xsl:if>

					<xsl:if test="doc:metadata/doc:element[@name='cg']/doc:element[@name='edition']/doc:element/doc:field[@name='value']">
						<edition>
							<xsl:value-of select="doc:metadata/doc:element[@name='cg']/doc:element[@name='edition']/doc:element/doc:field[@name='value']/text()"></xsl:value-of>
						</edition>
					</xsl:if>

					<xsl:if test="doc:metadata/doc:element[@name='dcterms']/doc:element[@name='publisher']/doc:element/doc:field[@name='value']">
						<publisher>
						    <xsl:value-of select="doc:metadata/doc:element[@name='dcterms']/doc:element[@name='publisher']/doc:element/doc:field[@name='value']/text()"></xsl:value-of>
						</publisher>
					</xsl:if>

					<dateIssued encoding="iso8601">
						<xsl:value-of select="doc:metadata/doc:element[@name='dcterms']/doc:element[@name='issued']/doc:element/doc:field[@name='value']/text()"></xsl:value-of>
					</dateIssued>

					<xsl:if test="doc:metadata/doc:element[@name='dc']/doc:element[@name='date']/doc:element[@name='accessioned']/doc:element/doc:field[@name='value']">
						<dateCaptured encoding="iso8601">
							<xsl:value-of select="doc:metadata/doc:element[@name='dc']/doc:element[@name='date']/doc:element[@name='accessioned']/doc:element/doc:field[@name='value']/text()"></xsl:value-of>
						</dateCaptured>
					</xsl:if>
				</originInfo>
			</xsl:if>

			<xsl:for-each select="doc:metadata/doc:element[@name='dcterms']/doc:element[@name='format']/doc:element/doc:field[@name='value']">
				<physicalDescription>
					<internetMediaType><xsl:value-of select="." /></internetMediaType>
				</physicalDescription>
			</xsl:for-each>

			<xsl:for-each select="doc:metadata/doc:element[@name='dcterms']/doc:element[@name='audience']/doc:element/doc:field[@name='value']">
				<targetAudience><xsl:value-of select="." /></targetAudience>
			</xsl:for-each>

			<!-- See: https://www.loc.gov/standards/mods/v3/modsjournal.xml -->
			<xsl:if test="doc:metadata/doc:element[@name='cg']/doc:element[@name='journal']/doc:element/doc:field[@name='value']">
				<relatedItem type="host">
					<titleInfo>
						<title>
							<xsl:value-of select="doc:metadata/doc:element[@name='cg']/doc:element[@name='journal']/doc:element/doc:field[@name='value']/text()"></xsl:value-of>
						</title>
					</titleInfo>

					<xsl:for-each select="doc:metadata/doc:element[@name='cg']/doc:element[@name='issn']/doc:element/doc:field[@name='value']">
						<identifier type="issn">
							<xsl:value-of select="." />
						</identifier>
					</xsl:for-each>

					<!-- This is a bit of a gamble because the <part> must encapsulate the issue, volume, pages, and date, and we assume at least one of them will exist so <part> isn't empty. -->
					<part>
					<xsl:if test="doc:metadata/doc:element[@name='cg']/doc:element[@name='issue']/doc:element/doc:field[@name='value']">
						<detail type="issue">
							<number>
								<xsl:value-of select="doc:metadata/doc:element[@name='cg']/doc:element[@name='issue']/doc:element/doc:field[@name='value']/text()"></xsl:value-of>
							</number>
							<caption>no.</caption>
						</detail>
					</xsl:if>
					<xsl:if test="doc:metadata/doc:element[@name='cg']/doc:element[@name='volume']/doc:element/doc:field[@name='value']">
						<detail type="volume">
							<number>
								<xsl:value-of select="doc:metadata/doc:element[@name='cg']/doc:element[@name='volume']/doc:element/doc:field[@name='value']/text()"></xsl:value-of>
							</number>
						</detail>
					</xsl:if>

					<xsl:if test="doc:metadata/doc:element[@name='dcterms']/doc:element[@name='issued']/doc:element/doc:field[@name='value']">
						<date>
							<xsl:value-of select="doc:metadata/doc:element[@name='dcterms']/doc:element[@name='issued']/doc:element/doc:field[@name='value']/text()"></xsl:value-of>
						</date>
					</xsl:if>

					</part>
				</relatedItem>
			</xsl:if>

			<xsl:if test="doc:metadata/doc:element[@name='dcterms']/doc:element[@name='bibliographicCitation']/doc:element/doc:field[@name='value']">
				<note type="citation">
					<xsl:value-of select="doc:metadata/doc:element[@name='dcterms']/doc:element[@name='bibliographicCitation']/doc:element/doc:field[@name='value']/text()"></xsl:value-of>
				</note>
			</xsl:if>

			<xsl:for-each select="doc:metadata/doc:element[@name='dc']/doc:element[@name='identifier']/doc:element/doc:field[@name='value']">
			<identifier>
				<xsl:attribute name="type">
					<xsl:value-of select="../@name" />
				</xsl:attribute>
				<xsl:value-of select="." />
			</identifier>
			</xsl:for-each>

			<xsl:for-each select="doc:metadata/doc:element[@name='cg']/doc:element[@name='identifier']/doc:element[@name='doi']/doc:element/doc:field[@name='value']">
				<identifier type="doi">
					<xsl:value-of select="." />
				</identifier>
			</xsl:for-each>

			<xsl:for-each select="doc:metadata/doc:element[@name='cg']/doc:element[@name='isbn']/doc:element/doc:field[@name='value']">
				<identifier type="isbn">
					<xsl:value-of select="." />
				</identifier>
			</xsl:for-each>

			<!-- See: https://www.loc.gov/standards/mods/userguide/abstract.html -->
			<xsl:for-each select="doc:metadata/doc:element[@name='dcterms']/doc:element[@name='abstract']/doc:element/doc:field[@name='value']">
				<abstract displayLabel="Content description"><xsl:value-of select="." /></abstract>
			</xsl:for-each>

            		<!-- Use rfc5645 because we currently have two-letter language codes -->
			<!-- See: https://www.loc.gov/standards/mods/userguide/language.html -->
			<!-- See: https://www.loc.gov/standards/sourcelist/language.html -->
			<xsl:for-each select="doc:metadata/doc:element[@name='dcterms']/doc:element[@name='language']/doc:element/doc:field[@name='value']">
			<language>
				<languageTerm type="code" authority="rfc5646"><xsl:value-of select="." /></languageTerm>
			</language>
			</xsl:for-each>

			<xsl:for-each select="doc:metadata/doc:element[@name='cg']/doc:element[@name='coverage']/doc:element[@name='region']/doc:element/doc:field[@name='value']">
				<subject>
					<hierarchicalGeographic>
						<region><xsl:value-of select="." /></region>
					</hierarchicalGeographic>
				</subject>
			</xsl:for-each>

			<xsl:for-each select="doc:metadata/doc:element[@name='cg']/doc:element[@name='coverage']/doc:element[@name='country']/doc:element/doc:field[@name='value']">
				<subject>
					<hierarchicalGeographic>
						<country><xsl:value-of select="." /></country>
					</hierarchicalGeographic>
				</subject>
			</xsl:for-each>

			<xsl:for-each select="doc:metadata/doc:element[@name='cg']/doc:element[@name='coverage']/doc:element[@name='subregion']/doc:element/doc:field[@name='value']">
				<subject>
					<hierarchicalGeographic>
						<area areaType="administrative unit"><xsl:value-of select="." /></area>
					</hierarchicalGeographic>
				</subject>
			</xsl:for-each>

			<!-- See: https://www.loc.gov/standards/mods/userguide/accesscondition.html -->
			<xsl:for-each select="doc:metadata/doc:element[@name='dcterms']/doc:element[@name='accessRights']/doc:element/doc:field[@name='value']">
				<accessCondition type="restriction on access"><xsl:value-of select="." /></accessCondition>
			</xsl:for-each>

			<xsl:for-each select="doc:metadata/doc:element[@name='dcterms']/doc:element[@name='license']/doc:element/doc:field[@name='value']">
				<accessCondition type="use and production"><xsl:value-of select="." /></accessCondition>
			</xsl:for-each>

			<xsl:for-each select="doc:metadata/doc:element[@name='dcterms']/doc:element[@name='subject']/doc:element/doc:field[@name='value']">
				<subject>
					<topic><xsl:value-of select="." /></topic>
				</subject>
			</xsl:for-each>

			<xsl:for-each select="doc:metadata/doc:element[@name='dc']/doc:element[@name='title']/doc:element/doc:field[@name='value']">
				<titleInfo>
				    <title><xsl:value-of select="." /></title>
				</titleInfo>
			</xsl:for-each>

		    	<!-- Only about 600 of these alternative titles in our repository -->
		   	<xsl:for-each select="doc:metadata/doc:element[@name='dc']/doc:element[@name='title']/doc:element[@name='alternative']/doc:element/doc:field[@name='value']">
		        <titleInfo>
		            <title type="alternative"><xsl:value-of select="." /></title>
		        </titleInfo>
			</xsl:for-each>

			<xsl:for-each select="doc:metadata/doc:element[@name='dcterms']/doc:element[@name='type']/doc:element/doc:field[@name='value']">
				<typeOfResource><xsl:value-of select="." /></typeOfResource>
			</xsl:for-each>
		</mods>
	</xsl:template>
</xsl:stylesheet>
