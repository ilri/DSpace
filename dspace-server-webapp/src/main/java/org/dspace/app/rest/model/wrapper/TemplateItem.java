package org.dspace.app.rest.model.wrapper;

import java.util.Date;
import java.util.List;

import org.dspace.content.Collection;
import org.dspace.content.Item;
import org.dspace.content.MetadataValue;

public class TemplateItem {
    private Item item;

    public TemplateItem(Item item) {
        if (item.getTemplateItemOf() == null) {
            throw new IllegalArgumentException();
        }

        this.item = item;
    }

    public Item getItem() {
        return this.item;
    }

    public List<MetadataValue> getMetadata() {
        return item.getMetadata();
    }

    public Object getID() {
        return item.getID();
    }

    public Date getLastModified() {
        return item.getLastModified();
    }

    public Collection getTemplateItemOf() {
        return item.getTemplateItemOf();
    }
}
