/**
 * The contents of this file are subject to the license and copyright
 * detailed in the LICENSE and NOTICE files at the root of the source
 * tree and available online at
 *
 * http://www.dspace.org/license/
 */
package org.dspace.app.rest;

import static org.hamcrest.Matchers.containsInAnyOrder;
import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.is;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.io.File;
import java.sql.SQLException;
import java.util.Iterator;
import java.util.List;

import org.dspace.app.rest.matcher.EntityTypeMatcher;
import org.dspace.app.rest.matcher.RelationshipTypeMatcher;
import org.dspace.app.rest.test.AbstractControllerIntegrationTest;
import org.dspace.content.EntityType;
import org.dspace.content.Relationship;
import org.dspace.content.RelationshipType;
import org.dspace.content.service.EntityTypeService;
import org.dspace.content.service.RelationshipService;
import org.dspace.content.service.RelationshipTypeService;
import org.dspace.services.ConfigurationService;
import org.h2.util.StringUtils;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.springframework.beans.factory.annotation.Autowired;

public class RelationshipTypeRestRepositoryIT extends AbstractControllerIntegrationTest {

    @Autowired
    private RelationshipTypeService relationshipTypeService;

    @Autowired
    private EntityTypeService entityTypeService;

    @Autowired
    private RelationshipService relationshipService;

    @Autowired
    private ConfigurationService configurationService;

    @Before
    public void setup() throws Exception {

        //Set up the database for the next test
        String pathToFile = configurationService.getProperty("dspace.dir") +
            File.separator + "config" + File.separator + "entities" + File.separator + "relationship-types.xml";
        runDSpaceScript("initialize-entities", "-f", pathToFile);
    }

    @After
    public void destroy() throws Exception {
        //Clean up the database for the next test
        context.turnOffAuthorisationSystem();
        List<RelationshipType> relationshipTypeList = relationshipTypeService.findAll(context);
        List<EntityType> entityTypeList = entityTypeService.findAll(context);
        List<Relationship> relationships = relationshipService.findAll(context);

        Iterator<Relationship> relationshipIterator = relationships.iterator();
        while (relationshipIterator.hasNext()) {
            Relationship relationship = relationshipIterator.next();
            relationshipIterator.remove();
            relationshipService.delete(context, relationship);
        }

        Iterator<RelationshipType> relationshipTypeIterator = relationshipTypeList.iterator();
        while (relationshipTypeIterator.hasNext()) {
            RelationshipType relationshipType = relationshipTypeIterator.next();
            relationshipTypeIterator.remove();
            relationshipTypeService.delete(context, relationshipType);
        }

        Iterator<EntityType> entityTypeIterator = entityTypeList.iterator();
        while (entityTypeIterator.hasNext()) {
            EntityType entityType = entityTypeIterator.next();
            entityTypeIterator.remove();
            entityTypeService.delete(context, entityType);
        }

        super.destroy();
    }

    @Test
    public void findAllRelationshipTypesTest() throws SQLException {
        assertEquals(9, relationshipTypeService.findAll(context).size());
    }

    @Test
    public void findPublicationPersonRelationshipType() throws SQLException {
        String leftTypeString = "Publication";
        String rightTypeString = "Person";
        String leftLabel = "isAuthorOfPublication";
        String rightLabel = "isPublicationOfAuthor";
        checkRelationshipType(leftTypeString, rightTypeString, leftLabel, rightLabel);
    }

    @Test
    public void findPublicationProjectRelationshipType() throws SQLException {
        String leftTypeString = "Publication";
        String rightTypeString = "Project";
        String leftLabel = "isProjectOfPublication";
        String rightLabel = "isPublicationOfProject";
        checkRelationshipType(leftTypeString, rightTypeString, leftLabel, rightLabel);
    }

    @Test
    public void findPublicationOrgUnitRelationshipType() throws SQLException {
        String leftTypeString = "Publication";
        String rightTypeString = "OrgUnit";
        String leftLabel = "isOrgUnitOfPublication";
        String rightLabel = "isPublicationOfOrgUnit";
        checkRelationshipType(leftTypeString, rightTypeString, leftLabel, rightLabel);
    }

    @Test
    public void findPersonProjectRelationshipType() throws SQLException {
        String leftTypeString = "Person";
        String rightTypeString = "Project";
        String leftLabel = "isProjectOfPerson";
        String rightLabel = "isPersonOfProject";
        checkRelationshipType(leftTypeString, rightTypeString, leftLabel, rightLabel);
    }

    @Test
    public void findPersonOrgUnitRelationshipType() throws SQLException {
        String leftTypeString = "Person";
        String rightTypeString = "OrgUnit";
        String leftLabel = "isOrgUnitOfPerson";
        String rightLabel = "isPersonOfOrgUnit";
        checkRelationshipType(leftTypeString, rightTypeString, leftLabel, rightLabel);
    }

    @Test
    public void findProjectOrgUnitRelationshipType() throws SQLException {
        String leftTypeString = "Project";
        String rightTypeString = "OrgUnit";
        String leftLabel = "isOrgUnitOfProject";
        String rightLabel = "isProjectOfOrgUnit";
        checkRelationshipType(leftTypeString, rightTypeString, leftLabel, rightLabel);
    }

    @Test
    public void findJournalJournalVolumeRelationshipType() throws SQLException {
        String leftTypeString = "Journal";
        String rightTypeString = "JournalVolume";
        String leftLabel = "isVolumeOfJournal";
        String rightLabel = "isJournalOfVolume";
        checkRelationshipType(leftTypeString, rightTypeString, leftLabel, rightLabel);
    }

    @Test
    public void findJournalVolumeJournalIssueRelationshipType() throws SQLException {
        String leftTypeString = "JournalVolume";
        String rightTypeString = "JournalIssue";
        String leftLabel = "isIssueOfJournalVolume";
        String rightLabel = "isJournalVolumeOfIssue";
        checkRelationshipType(leftTypeString, rightTypeString, leftLabel, rightLabel);
    }

    private void checkRelationshipType(String leftType, String rightType, String leftLabel, String rightLabel)
        throws SQLException {
        RelationshipType relationshipType = relationshipTypeService
            .findbyTypesAndLabels(context, entityTypeService.findByEntityType(context, leftType),
                                  entityTypeService.findByEntityType(context, rightType),
                                  leftLabel, rightLabel);
        assertNotNull(relationshipType);
        assertEquals(entityTypeService.findByEntityType(context, leftType),
                     relationshipType.getLeftType());
        assertEquals(entityTypeService.findByEntityType(context, rightType),
                     relationshipType.getRightType());
        assertEquals(leftLabel, relationshipType.getLeftLabel());
        assertEquals(rightLabel, relationshipType.getRightLabel());
    }

    @Test
    public void getAllRelationshipTypesEndpointTest() throws Exception {
        //When we call this facets endpoint
        List<RelationshipType> relationshipTypes = relationshipTypeService.findAll(context);

        getClient().perform(get("/api/core/relationshiptypes"))

                   //We expect a 200 OK status
                   .andExpect(status().isOk())
                   //The type has to be 'discover'
                   .andExpect(jsonPath("$.page.totalElements", is(9)))
                   //There needs to be a self link to this endpoint
                   .andExpect(jsonPath("$._links.self.href", containsString("api/core/relationshiptypes")))
                   //We have 4 facets in the default configuration, they need to all be present in the embedded section
                   .andExpect(jsonPath("$._embedded.relationshiptypes", containsInAnyOrder(
                       RelationshipTypeMatcher.matchRelationshipTypeEntry(relationshipTypes.get(0)),
                       RelationshipTypeMatcher.matchRelationshipTypeEntry(relationshipTypes.get(1)),
                       RelationshipTypeMatcher.matchRelationshipTypeEntry(relationshipTypes.get(2)),
                       RelationshipTypeMatcher.matchRelationshipTypeEntry(relationshipTypes.get(3)),
                       RelationshipTypeMatcher.matchRelationshipTypeEntry(relationshipTypes.get(4)),
                       RelationshipTypeMatcher.matchRelationshipTypeEntry(relationshipTypes.get(5)),
                       RelationshipTypeMatcher.matchRelationshipTypeEntry(relationshipTypes.get(6)),
                       RelationshipTypeMatcher.matchRelationshipTypeEntry(relationshipTypes.get(7)),
                       RelationshipTypeMatcher.matchRelationshipTypeEntry(relationshipTypes.get(8)))
                   ));
    }

    @Test
    public void entityTypeForPublicationPersonRelationshipTypeTest() throws Exception {

        List<RelationshipType> relationshipTypes = relationshipTypeService.findAll(context);

        RelationshipType foundRelationshipType = null;
        for (RelationshipType relationshipType : relationshipTypes) {
            if (StringUtils.equals(relationshipType.getLeftLabel(), "isAuthorOfPublication") && StringUtils
                .equals(relationshipType.getRightLabel(), "isPublicationOfAuthor")) {
                foundRelationshipType = relationshipType;
                break;
            }
        }

        if (foundRelationshipType != null) {
            getClient().perform(get("/api/core/relationshiptypes/" + foundRelationshipType.getId()))
                       .andExpect(jsonPath("$._embedded.leftType",
                                           EntityTypeMatcher.matchEntityTypeEntryForLabel("Publication")))
                       .andExpect(
                           jsonPath("$._embedded.rightType", EntityTypeMatcher.matchEntityTypeEntryForLabel("Person")));
        } else {
            throw new Exception("RelationshipType not found for isIssueOfJournalVolume");
        }

    }

    @Test
    public void cardinalityOnAuthorPublicationRelationshipTypesTest() throws Exception {
        RelationshipType relationshipType = relationshipTypeService
            .findbyTypesAndLabels(context, entityTypeService.findByEntityType(context, "Publication"),
                                  entityTypeService.findByEntityType(context, "Person"), "isAuthorOfPublication",
                                  "isPublicationOfAuthor");
        assertEquals(0, relationshipType.getLeftMinCardinality());
        assertEquals(0, relationshipType.getRightMinCardinality());
        assertEquals(Integer.MAX_VALUE, relationshipType.getLeftMaxCardinality());
        assertEquals(Integer.MAX_VALUE, relationshipType.getRightMaxCardinality());

        getClient().perform(get("/api/core/relationshiptypes/" + relationshipType.getId()))
                   .andExpect(jsonPath("$.leftMinCardinality", is(0)))
                   .andExpect(jsonPath("$.rightMinCardinality", is(0)))
                   .andExpect(jsonPath("$.leftMaxCardinality", is(Integer.MAX_VALUE)))
                   .andExpect(jsonPath("$.rightMaxCardinality", is(Integer.MAX_VALUE)));

    }

    @Test
    public void entityTypeForIssueJournalRelationshipTypeTest() throws Exception {

        List<RelationshipType> relationshipTypes = relationshipTypeService.findAll(context);

        RelationshipType foundRelationshipType = null;
        for (RelationshipType relationshipType : relationshipTypes) {
            if (StringUtils.equals(relationshipType.getLeftLabel(), "isIssueOfJournalVolume") && StringUtils
                .equals(relationshipType.getRightLabel(), "isJournalVolumeOfIssue")) {
                foundRelationshipType = relationshipType;
                break;
            }
        }

        if (foundRelationshipType != null) {
            getClient().perform(get("/api/core/relationshiptypes/" + foundRelationshipType.getId()))
                       .andExpect(jsonPath("$._embedded.leftType",
                                           EntityTypeMatcher.matchEntityTypeEntryForLabel("JournalVolume")))
                       .andExpect(jsonPath("$._embedded.rightType",
                                           EntityTypeMatcher.matchEntityTypeEntryForLabel("JournalIssue")));
        } else {
            throw new Exception("RelationshipType not found for isIssueOfJournalVolume");
        }

    }

    @Test
    public void cardinalityOnIssueJournalJournalVolumeRelationshipTypesTest() throws Exception {
        RelationshipType relationshipType = relationshipTypeService
            .findbyTypesAndLabels(context, entityTypeService.findByEntityType(context, "JournalVolume"),
                                  entityTypeService.findByEntityType(context, "JournalIssue"), "isIssueOfJournalVolume",
                                  "isJournalVolumeOfIssue");
        assertEquals(0, relationshipType.getLeftMinCardinality());
        assertEquals(1, relationshipType.getRightMinCardinality());
        assertEquals(Integer.MAX_VALUE, relationshipType.getLeftMaxCardinality());
        assertEquals(1, relationshipType.getRightMaxCardinality());

        getClient().perform(get("/api/core/relationshiptypes/" + relationshipType.getId()))
                   .andExpect(jsonPath("$.leftMinCardinality", is(0)))
                   .andExpect(jsonPath("$.rightMinCardinality", is(1)))
                   .andExpect(jsonPath("$.leftMaxCardinality", is(Integer.MAX_VALUE)))
                   .andExpect(jsonPath("$.rightMaxCardinality", is(1)));

    }


}