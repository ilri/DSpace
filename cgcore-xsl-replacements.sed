#!/usr/bin/env -S sed -i -f

# Replacements

# dcterms.title
s/"dim:field\[@element='title'\]/"dim:field[@mdschema='dcterms' and @element='title']/g
s/(dim:field\[@element='title'\]/(dim:field[@mdschema='dcterms' and @element='title']/g
s/::dim:field\[@element='title'\]/::dim:field[@mdschema='dcterms' and @element='title']/g
s/':dc.title'/':dcterms.title'/g
# dcterms.bibliographicCitation
s/dim:field\[@element='identifier' and @qualifier='citation'\]/dim:field[@mdschema='dcterms' and @element='bibliographicCitation']/g
# dcterms.creator
s/dim:field\[@element='contributor'\]\[@qualifier='author'\]/dim:field[@mdschema='dcterms' and @element='creator']/g
s/dim:field\[@element='creator'/dim:field[@mdschema='dcterms' and @element='creator'/g
s/':dc.contributor.author'/':dcterms.creator'/g
# dcterms.issued
s/dim:field\[@element='date' and @qualifier='issued'\]/dim:field[@mdschema='dcterms' and @element='issued']/g
s/dim:field\[@element='date' and @qualifier='issued' and descendant::text()\]/dim:field[@mdschema='dcterms' and @element='issued' and descendant::text()]/g
s/:dc.date.issued/:dcterms.issued/g
# dcterms.type
s/dim:field\[@element = 'type'\]/dim:field[@mdschema='dcterms' and @element = 'type']/g
s/dim:field\[@element='type'/dim:field[@mdschema='dcterms' and @element='type'/g
s/:dc.type/:dcterms.type/g
# dcterms.accessRights
s/dim:field\[@mdschema='cg' and @element = 'identifier' and @qualifier='status'\]/dim:field[@mdschema='dcterms' and @element = 'accessRights']/g
s/dim:field\[@mdschema='cg' and @element='identifier' and @qualifier='status'/dim:field[@mdschema='dcterms' and @element='accessRights'/g
s/:cg.identifier.status/:dcterms.accessRights/g
# dcterms.description
s/dim:field\[@element='description'\]\[not(@qualifier)\]/dim:field[@mdschema='dcterms' and @element='description'][not(@qualifier)]/g
# dcterms.subject
s/dim:field\[@element='subject'/dim:field[@mdschema='dcterms' and @element='subject'/g
# cg.contributor.donor
s/dim:field\[@element='description' and @qualifier='sponsorship'/dim:field[@mdschema='cg' and @element='contributor' and @qualifier='donor'/g
# cg.hasMetadata
s/dim:field\[@mdschema='cg' and @element='identifier' and @qualifier='dataurl'/dim:field[@mdschema='cg' and @element='hasMetadata'/g
s/dim:field\[ @mdschema='cg' and @element='identifier' and @qualifier='dataurl'/dim:field[ @mdschema='cg' and @element='hasMetadata'/g
# dcterms.abstract
s/dim:field\[@element='description' and @qualifier='abstract'\]/dim:field[@mdschema='dcterms' and @element='abstract']/g
# cg.creator.identifier 
s/dim:field\[@mdschema='cg' and @element='creator'\]\[@qualifier='id'/dim:field[@mdschema='cg' and @element='creator'][@qualifier='identifier'/g
s/cg\.creator\.id/cg.creator.identifier/g
# dcterms.language
s/dim:field\[@element='language' and @qualifier='iso'/dim:field[@mdschema='dcterms' and @element='language'/g
# cg.peer-reviewed
s/dim:field\[@element='description' and @qualifier='version'/dim:field[@mdschema='cg' and @element='peer-reviewed'/g
# dcterms.license
s/dim:field\[@element='rights'\]\[not(@qualifier)\]/dim:field[@mdschema='dcterms' and @element='license']/g


# Additions

## Add dcterms.relation in item-view-DIM-helper.xsl (make sure source pattern is
## long enough so that it doesn't match if we run the replacements again)
206 s/dim:field\[@mdschema='cg' and @element='link' \] or dim:field\[@mdschema='cg'/dim:field[@mdschema='cg' and @element='link' ] or dim:field[@mdschema='dcterms' and @element='relation' ] or dim:field[@mdschema='cg'/

# Removals

## dc.contributor.author will no longer exist so just remove this
s/dim:field\[@element='contributor'\]\[@qualifier='author' and descendant::text()\] or //g
