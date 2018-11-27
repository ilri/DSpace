/**
 * The contents of this file are subject to the license and copyright
 * detailed in the LICENSE and NOTICE files at the root of the source
 * tree and available online at
 *
 * http://www.dspace.org/license/
 */
package org.dspace.app.rest.model;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonIgnore;
import org.dspace.app.rest.RelationshipTypeRestController;

public class RelationshipTypeRestWrapper implements RestAddressableModel {

    @JsonIgnore
    private List<RelationshipTypeRest> relationshipTypeRestList;

    private String entityTypeLabel;
    private Integer entityTypeId;



    public List<RelationshipTypeRest> getRelationshipTypeRestList() {
        return relationshipTypeRestList;
    }

    public void setRelationshipTypeRestList(
        List<RelationshipTypeRest> relationshipTypeRestList) {
        this.relationshipTypeRestList = relationshipTypeRestList;
    }

    public String getCategory() {
        return "core";
    }

    public Class getController() {
        return RelationshipTypeRestController.class;
    }

    public String getType() {
        return "relationshiptype";
    }

    public String getEntityTypeLabel() {
        return entityTypeLabel;
    }

    public void setEntityTypeLabel(String label) {
        this.entityTypeLabel = label;
    }

    public Integer getEntityTypeId() {
        return entityTypeId;
    }

    public void setEntityTypeId(Integer entityTypeId) {
        this.entityTypeId = entityTypeId;
    }
}