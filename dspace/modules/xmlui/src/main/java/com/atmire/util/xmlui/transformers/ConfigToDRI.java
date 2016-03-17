package com.atmire.util.xmlui.transformers;

import org.apache.commons.lang3.StringUtils;
import org.apache.log4j.Logger;
import org.dspace.app.xmlui.cocoon.AbstractDSpaceTransformer;
import org.dspace.app.xmlui.wing.WingException;
import org.dspace.app.xmlui.wing.element.PageMeta;
import org.dspace.core.ConfigurationManager;

import java.util.Map;
import java.util.Properties;

/**
 * Created by: Antoine Snyers (antoine at atmire dot com)
 * Date: 04 Dec 2015
 */
public class ConfigToDRI extends AbstractDSpaceTransformer {

    /**
     * log4j logger
     */
    private static final Logger log = Logger.getLogger(ConfigToDRI.class);

    /**
     * Initialize the page metadata & breadcrumb trail
     */
    @Override
    public void addPageMeta(PageMeta pageMeta) throws WingException {

        Properties propertiesToDri = ConfigurationManager.getProperties("config-to-dri");
        for (Map.Entry<Object, Object> entry : propertiesToDri.entrySet()) {
            try {
                String name = (String) entry.getKey();
                boolean include = Boolean.parseBoolean((String) entry.getValue());
                if (include) {
                    String module = StringUtils.substringBefore(name, ".");
                    String property = StringUtils.substringAfter(name, ".");
                    if (StringUtils.isNotBlank(property)) {
                        if ("dspace".equals(module) || "".equals(module)) {
                            module = null;
                        }
                        String propertyValue = ConfigurationManager.getProperty(module, property);
                        pageMeta.addMetadata("config", name).addContent(propertyValue);
                    }

                }
            } catch (Exception e) {
                log.error("Could not include config-to-dri property " + entry.getKey());
            }
        }
    }

}
