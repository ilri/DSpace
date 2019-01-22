/**
 * The contents of this file are subject to the license and copyright
 * detailed in the LICENSE and NOTICE files at the root of the source
 * tree and available online at
 *
 * http://www.dspace.org/license/
 */
package org.dspace.app.rest;

import javax.servlet.http.HttpServletRequest;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.dspace.app.rest.link.HalLinkService;
import org.dspace.app.rest.model.RootRest;
import org.dspace.app.rest.model.hateoas.RootResource;
import org.dspace.app.rest.repository.RootRestRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

/**
 * This is the main entry point of the new REST API. Its responsibility is to
 * provide a consistent behaviors for all the exposed resources in terms of
 * returned HTTP codes, endpoint URLs, HTTP verbs to methods translation, etc.
 * It delegates to the repository the business logic
 *
 * @author Andrea Bollini (andrea.bollini at 4science.it)
 */
@RestController
@RequestMapping("/api")
public class RootRestResourceController {

    @Autowired
    DiscoverableEndpointsService discoverableEndpointsService;

    @Autowired
    HalLinkService halLinkService;

    @Autowired
    RootRestRepository rootRestRepository;

    private static Logger log = LogManager.getLogger();

    @RequestMapping(method = RequestMethod.GET)
    public RootResource listDefinedEndpoint(HttpServletRequest request) {

        RootRest rootRest = rootRestRepository.getRoot();
        RootResource rootResource = new RootResource(rootRest);
        halLinkService.addLinks(rootResource);

        return rootResource;
    }
}