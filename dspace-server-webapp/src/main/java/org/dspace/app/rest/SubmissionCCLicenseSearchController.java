/**
 * The contents of this file are subject to the license and copyright
 * detailed in the LICENSE and NOTICE files at the root of the source
 * tree and available online at
 *
 * http://www.dspace.org/license/
 */
package org.dspace.app.rest;

import java.util.HashMap;
import java.util.Map;
import javax.servlet.ServletRequest;

import org.apache.commons.lang3.StringUtils;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.dspace.app.rest.exception.DSpaceBadRequestException;
import org.dspace.app.rest.model.SubmissionCCLicenseRest;
import org.dspace.app.rest.utils.Utils;
import org.dspace.license.service.CreativeCommonsService;
import org.dspace.services.RequestService;
import org.dspace.utils.DSpace;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.rest.webmvc.ResourceNotFoundException;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.RestController;

/**
 * This controller is responsible for searching the CC License URI
 */
@RestController
@RequestMapping("/api/" + SubmissionCCLicenseRest.CATEGORY + "/" + SubmissionCCLicenseRest.PLURAL + "/search" +
        "/rightsByQuestions")
public class SubmissionCCLicenseSearchController {

    private static final Logger log = LogManager.getLogger();

    @Autowired
    protected Utils utils;

    @Autowired
    protected CreativeCommonsService creativeCommonsService;

    protected RequestService requestService = new DSpace().getRequestService();

    /**
     * Retrieves the CC License URI based on the license ID and answers in the field questions, provided as parameters
     * to this request
     *
     * @return the CC License URI as a string
     */
    @RequestMapping(method = RequestMethod.GET)
    @ResponseBody
    public String findByRightsByQuestions() {
        ServletRequest servletRequest = requestService.getCurrentRequest()
                                                      .getServletRequest();
        Map<String, String[]> requestParameterMap = servletRequest
                .getParameterMap();
        Map<String, String> parameterMap = new HashMap<>();
        String licenseId = servletRequest.getParameter("license");
        if (StringUtils.isBlank(licenseId)) {
            throw new DSpaceBadRequestException(
                    "A \"license\" parameter needs to be provided.");
        }
        for (String parameter : requestParameterMap.keySet()) {
            if (StringUtils.startsWith(parameter, "answer_")) {
                String field = StringUtils.substringAfter(parameter, "answer_");
                String answer = "";
                if (requestParameterMap.get(parameter).length > 0) {
                    answer = requestParameterMap.get(parameter)[0];
                }
                parameterMap.put(field, answer);
            }
        }

        Map<String, String> fullParamMap = creativeCommonsService.retrieveFullAnswerMap(licenseId, parameterMap);
        if (fullParamMap == null) {
            throw new ResourceNotFoundException("No CC License could be matched on the provided ID: " + licenseId);
        }
        boolean licenseContainsCorrectInfo = creativeCommonsService.verifyLicenseInformation(licenseId, fullParamMap);
        if (!licenseContainsCorrectInfo) {
            throw new DSpaceBadRequestException(
                    "The provided answers do not match the required fields for the provided license.");
        }

        String licenseUri = creativeCommonsService.retrieveLicenseUri(licenseId, fullParamMap);

        if (StringUtils.isBlank(licenseUri)) {
            throw new ResourceNotFoundException("No CC License URI could be found for ID: " + licenseId);
        }
        return licenseUri;
    }
}