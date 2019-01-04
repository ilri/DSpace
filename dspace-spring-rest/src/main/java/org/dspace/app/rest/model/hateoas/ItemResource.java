/**
 * The contents of this file are subject to the license and copyright
 * detailed in the LICENSE and NOTICE files at the root of the source
 * tree and available online at
 *
 * http://www.dspace.org/license/
 */
package org.dspace.app.rest.model.hateoas;

import java.util.LinkedList;
import java.util.List;
import java.util.Map;

import org.dspace.app.rest.link.relation.RelationshipResourceWrapperHalLinkFactory;
import org.dspace.app.rest.model.ItemRest;
import org.dspace.app.rest.model.RelationshipRest;
import org.dspace.app.rest.model.RestAddressableModel;
import org.dspace.app.rest.model.hateoas.annotations.RelNameDSpaceResource;
import org.dspace.app.rest.utils.Utils;
import org.springframework.data.domain.PageImpl;

/**
 * Item Rest HAL Resource. The HAL Resource wraps the REST Resource
 * adding support for the links and embedded resources
 *
 * @author Andrea Bollini (andrea.bollini at 4science.it)
 */
@RelNameDSpaceResource(ItemRest.NAME)
public class ItemResource extends DSpaceResource<ItemRest> {
    public ItemResource(ItemRest item, Utils utils, String... rels) {
        super(item, utils, rels);
        if (item.getRelationshipsByRelationshipType() != null) {
            for (Map.Entry<String, List<RelationshipRest>> entry :
                item.getRelationshipsByRelationshipType().entrySet()) {
                List<RelationshipResource> relationshipResources = new LinkedList<>();
                for (RelationshipRest relationshipRest : entry.getValue()) {
                    relationshipResources.add(new RelationshipResource(relationshipRest, utils));
                }
                int begin = 0;
                int end = relationshipResources.size() < 20 ? relationshipResources.size() : 20;
                relationshipResources = relationshipResources.subList(begin, end);
                PageImpl<RestAddressableModel> page = new PageImpl(relationshipResources);
                RelationshipResourceWrapperHalLinkFactory linkFactory = new RelationshipResourceWrapperHalLinkFactory();
                EmbeddedPage wrapObject = new EmbeddedPage(
                    linkFactory.buildRelationshipWithLabelLink(entry.getKey(), item.getId()).toUriString(), page,
                    relationshipResources, RelationshipRest.PLURAL_NAME);
                embedResource(entry.getKey(), wrapObject);

            }
        }
    }
}
