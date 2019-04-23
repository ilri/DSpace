<!--

    The contents of this file are subject to the license and copyright
    detailed in the LICENSE and NOTICE files at the root of the source
    tree and available online at

    http://www.dspace.org/license/

-->

<!--
    Main structure of the page, determines where
    header, footer, body, navigation are structurally rendered.
    Rendering of the header, footer, trail and alerts

    Author: art.lowel at atmire.com
    Author: lieven.droogmans at atmire.com
    Author: ben at atmire.com
    Author: Alexey Maslov

-->

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

    <!--
        Requested Page URI. Some functions may alter behavior of processing depending if URI matches a pattern.
        Specifically, adding a static page will need to override the DRI, to directly add content.
    -->
    <xsl:variable name="request-uri" select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='request'][@qualifier='URI']"/>

    <!--
        The starting point of any XSL processing is matching the root element. In DRI the root element is document,
        which contains a version attribute and three top level elements: body, options, meta (in that order).

        This template creates the html document, giving it a head and body. A title and the CSS style reference
        are placed in the html head, while the body is further split into several divs. The top-level div
        directly under html body is called "ds-main". It is further subdivided into:
            "ds-header"  - the header div containing title, subtitle, trail and other front matter
            "ds-body"    - the div containing all the content of the page; built from the contents of dri:body
            "ds-options" - the div with all the navigation and actions; built from the contents of dri:options
            "ds-footer"  - optional footer div, containing misc information

        The order in which the top level divisions appear may have some impact on the design of CSS and the
        final appearance of the DSpace page. While the layout of the DRI schema does favor the above div
        arrangement, nothing is preventing the designer from changing them around or adding new ones by
        overriding the dri:document template.
    -->
    <xsl:template match="dri:document">

        <xsl:choose>
            <xsl:when test="not($isModal)">


            <xsl:text disable-output-escaping='yes'>&lt;!DOCTYPE html&gt;
            </xsl:text>
            <xsl:text disable-output-escaping="yes">&lt;!--[if lt IE 7]&gt; &lt;html class=&quot;no-js lt-ie9 lt-ie8 lt-ie7&quot; lang=&quot;en&quot;&gt; &lt;![endif]--&gt;
            &lt;!--[if IE 7]&gt;    &lt;html class=&quot;no-js lt-ie9 lt-ie8&quot; lang=&quot;en&quot;&gt; &lt;![endif]--&gt;
            &lt;!--[if IE 8]&gt;    &lt;html class=&quot;no-js lt-ie9&quot; lang=&quot;en&quot;&gt; &lt;![endif]--&gt;
            &lt;!--[if gt IE 8]&gt;&lt;!--&gt; &lt;html class=&quot;no-js&quot; lang=&quot;en&quot;&gt; &lt;!--&lt;![endif]--&gt;
            </xsl:text>

                <!-- First of all, build the HTML head element -->

                <xsl:call-template name="buildHead"/>

                <!-- Then proceed to the body -->
                <body>
                    <xsl:call-template name="bodyAttributes"/>
                    <!-- Prompt IE 6 users to install Chrome Frame. Remove this if you support IE 6.
                   chromium.org/developers/how-tos/chrome-frame-getting-started -->
                    <!--[if lt IE 7]><p class=chromeframe>Your browser is <em>ancient!</em> <a href="http://browsehappy.com/">Upgrade to a different browser</a> or <a href="http://www.google.com/chromeframe/?redirect=true">install Google Chrome Frame</a> to experience this site.</p><![endif]-->
                    <xsl:choose>
                        <xsl:when
                                test="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='framing'][@qualifier='popup']">
                            <xsl:apply-templates select="dri:body/*"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="buildHeader"/>
                            <xsl:call-template name="buildTrail"/>
                            <!--javascript-disabled warning, will be invisible if javascript is enabled-->
                            <div id="no-js-warning-wrapper" class="hidden">
                                <div id="no-js-warning">
                                    <div class="notice failure">
                                        <xsl:text>JavaScript is disabled for your browser. Some features of this site may not work without it.</xsl:text>
                                    </div>
                                </div>
                            </div>

                            <div id="main-container" class="container">

                                <div class="row row-offcanvas row-offcanvas-right">
                                    <div class="horizontal-slider clearfix">
                                        <div class="col-xs-12 col-sm-12 col-md-9 main-content">
                                            <xsl:apply-templates select="*[not(self::dri:options)]"/>

                                            <div class="visible-xs visible-sm">
                                                <xsl:call-template name="buildFooter"/>
                                            </div>
                                        </div>
                                        <div class="col-xs-6 col-sm-3 sidebar-offcanvas" id="sidebar" role="navigation">
                                            <xsl:apply-templates select="dri:options"/>
                                        </div>

                                    </div>
                                </div>

                                <!--
                            The footer div, dropping whatever extra information is needed on the page. It will
                            most likely be something similar in structure to the currently given example. -->
                                <div class="hidden-xs hidden-sm">
                                    <xsl:call-template name="buildFooter"/>
                                </div>
                            </div>


                        </xsl:otherwise>
                    </xsl:choose>
                    <!-- Javascript at the bottom for fast page loading -->
                    <xsl:call-template name="addJavascript"/>
                </body>
                <xsl:text disable-output-escaping="yes">&lt;/html&gt;</xsl:text>

            </xsl:when>
            <xsl:otherwise>
                <!-- This is only a starting point. If you want to use this feature you need to implement
                JavaScript code and a XSLT template by yourself. Currently this is used for the DSpace Value Lookup -->
                <xsl:apply-templates select="dri:body" mode="modal"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="bodyAttributes">

        <xsl:if test="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='config'][@qualifier='atmire-cua.auto-open-statlets'][text()='true']">
            <xsl:attribute name="class">
                <xsl:text>auto-open-statlets</xsl:text>
            </xsl:attribute>
        </xsl:if>

    </xsl:template>

    <!-- The HTML head element contains references to CSS as well as embedded JavaScript code. Most of this
    information is either user-provided bits of post-processing (as in the case of the JavaScript), or
    references to stylesheets pulled directly from the pageMeta element. -->
    <xsl:template name="buildHead">
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>

            <!-- Use the .htaccess and remove these lines to avoid edge case issues.
             More info: h5bp.com/i/378 -->
            <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1"/>

            <!-- Mobile viewport optimized: h5bp.com/viewport -->
            <meta name="viewport" content="width=device-width,initial-scale=1"/>

            <link rel="shortcut icon">
                <xsl:attribute name="href">
                    <xsl:value-of select="$theme-path"/>
                    <xsl:text>images/favicon.ico</xsl:text>
                </xsl:attribute>
            </link>
            <link rel="apple-touch-icon">
                <xsl:attribute name="href">
                    <xsl:value-of select="$theme-path"/>
                    <xsl:text>images/apple-touch-icon.png</xsl:text>
                </xsl:attribute>
            </link>

            <meta name="Generator">
                <xsl:attribute name="content">
                    <xsl:text>DSpace</xsl:text>
                    <xsl:if test="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='dspace'][@qualifier='version']">
                        <xsl:text> </xsl:text>
                        <xsl:value-of select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='dspace'][@qualifier='version']"/>
                    </xsl:if>
                </xsl:attribute>
            </meta>

            <!-- Add stylesheets -->
            <!-- Use the theme path as provided by the metadata, not from the theme-path variable, as this needs to be able to take the child-themes without flickering -->
            <xsl:variable name="current-theme-path">
                <xsl:value-of select="concat($context-path,'/themes/',$pagemeta/dri:metadata[@element='theme'][@qualifier='path'])"/>
            </xsl:variable>

            <!--TODO figure out a way to include these in the concat & minify-->
            <xsl:for-each select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='stylesheet']">
                <link rel="stylesheet" type="text/css">
                    <xsl:attribute name="media">
                        <xsl:value-of select="@qualifier"/>
                    </xsl:attribute>
                    <xsl:attribute name="href">
                        <xsl:value-of select="$current-theme-path"/>
                        <xsl:value-of select="."/>
                    </xsl:attribute>
                </link>
            </xsl:for-each>

            <link rel="stylesheet" href="{concat($current-theme-path, 'styles/main.css')}"/>

            <!-- Add syndication feeds -->
            <xsl:for-each select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='feed']">
                <link rel="alternate" type="application">
                    <xsl:attribute name="type">
                        <xsl:text>application/</xsl:text>
                        <xsl:value-of select="@qualifier"/>
                    </xsl:attribute>
                    <xsl:attribute name="href">
                        <xsl:value-of select="."/>
                    </xsl:attribute>
                </link>
            </xsl:for-each>

            <!--  Add OpenSearch auto-discovery link -->
            <xsl:if test="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='opensearch'][@qualifier='shortName']">
                <link rel="search" type="application/opensearchdescription+xml">
                    <xsl:attribute name="href">
                        <xsl:value-of select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='request'][@qualifier='scheme']"/>
                        <xsl:text>://</xsl:text>
                        <xsl:value-of select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='request'][@qualifier='serverName']"/>
                        <xsl:text>:</xsl:text>
                        <xsl:value-of select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='request'][@qualifier='serverPort']"/>
                        <xsl:value-of select="$context-path"/>
                        <xsl:text>/</xsl:text>
                        <xsl:value-of select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='opensearch'][@qualifier='context']"/>
                        <xsl:text>description.xml</xsl:text>
                    </xsl:attribute>
                    <xsl:attribute name="title" >
                        <xsl:value-of select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='opensearch'][@qualifier='shortName']"/>
                    </xsl:attribute>
                </link>
            </xsl:if>

            <!-- The following javascript removes the default text of empty text areas when they are focused on or submitted -->
            <!-- There is also javascript to disable submitting a form when the 'enter' key is pressed. -->
            <script>
                //Clear default text of emty text areas on focus
                function tFocus(element)
                {
                if (element.value == '<i18n:text>xmlui.dri2xhtml.default.textarea.value</i18n:text>'){element.value='';}
                }
                //Clear default text of emty text areas on submit
                function tSubmit(form)
                {
                var defaultedElements = document.getElementsByTagName("textarea");
                for (var i=0; i != defaultedElements.length; i++){
                if (defaultedElements[i].value == '<i18n:text>xmlui.dri2xhtml.default.textarea.value</i18n:text>'){
                defaultedElements[i].value='';}}
                }
                //Disable pressing 'enter' key to submit a form (otherwise pressing 'enter' causes a submission to start over)
                function disableEnterKey(e)
                {
                var key;

                if(window.event)
                key = window.event.keyCode;     //Internet Explorer
                else
                key = e.which;     //Firefox and Netscape

                if(key == 13)  //if "Enter" pressed, then disable!
                return false;
                else
                return true;
                }
            </script>

            <xsl:text disable-output-escaping="yes">&lt;!--[if lt IE 9]&gt;
                &lt;script src="</xsl:text><xsl:value-of select="concat($theme-path, 'vendor/html5shiv/dist/html5shiv.js')"/><xsl:text disable-output-escaping="yes">"&gt;&#160;&lt;/script&gt;
                &lt;script src="</xsl:text><xsl:value-of select="concat($theme-path, 'vendor/respond/respond.min.js')"/><xsl:text disable-output-escaping="yes">"&gt;&#160;&lt;/script&gt;
                &lt;![endif]--&gt;</xsl:text>

            <!-- Modernizr enables HTML5 elements & feature detects -->
            <script src="{concat($theme-path, 'vendor/modernizr/modernizr.js')}">&#160;</script>

            <!-- Add the title in -->
            <xsl:variable name="page_title" select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='title'][last()]" />
            <title>
                <xsl:choose>
                    <xsl:when test="starts-with($request-uri, 'page/about')">
                        <i18n:text>xmlui.mirage2.page-structure.aboutThisRepository</i18n:text>
                    </xsl:when>
                    <xsl:when test="starts-with($request-uri, 'page/privacy')">
                        <i18n:text>xmlui.mirage2.page-structure.privacyStatement</i18n:text>
                    </xsl:when>
                    <xsl:when test="not($page_title)">
                        <xsl:text>  </xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:copy-of select="$page_title/node()" />
                    </xsl:otherwise>
                </xsl:choose>
            </title>

            <!-- Head metadata in item pages -->
            <xsl:if test="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='xhtml_head_item']">
                <xsl:value-of select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='xhtml_head_item']"
                              disable-output-escaping="yes"/>
            </xsl:if>

            <!-- Add all Google Scholar Metadata values -->
            <xsl:for-each select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[substring(@element, 1, 9) = 'citation_']">
                <meta name="{@element}" content="{.}"></meta>
            </xsl:for-each>

            <!-- Add MathJAX JS library to render scientific formulas-->
            <xsl:if test="confman:getProperty('webui.browse.render-scientific-formulas') = 'true'">
                <script type="text/x-mathjax-config">
                    MathJax.Hub.Config({
                    tex2jax: {
                    inlineMath: [['$','$'], ['\\(','\\)']],
                    ignoreClass: "detail-field-data|detailtable|exception"
                    },
                    TeX: {
                    Macros: {
                    AA: '{\\mathring A}'
                    }
                    }
                    });
                </script>
                <script type="text/javascript" src="//cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML">&#160;</script>
            </xsl:if>

        </head>
    </xsl:template>


    <!-- The header (distinct from the HTML head element) contains the title, subtitle, login box and various
        placeholders for header images -->
    <xsl:template name="buildHeader">


        <header>
            <div class="navbar navbar-default navbar-static-top" role="navigation">
                <div class="container">
                    <div class="row">
                    <div class="navbar-header">




                            <span>
                                <a class="navbar-brand" target="_blank">
                                    <xsl:attribute name="href">
                                        <xsl:value-of select="$headerLogoLink"/>
                                    </xsl:attribute>
                                <!-- allow child themes to use a different logo by setting $headerLogoSrc in theme.xsl -->
                                <img src="{concat($theme-path, $headerLogoSrc)}" />
                            </a>
                            </span>
                                <span class="headerInfoName">CGSpace</span>
                                <span class="headerInfoText">A Repository of Agricultural Research Outputs</span>




                        <div class="navbar-header pull-right visible-xs hidden-sm hidden-md hidden-lg">
                            <ul class="nav nav-pills pull-left ">

                                <xsl:if test="count(/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='page'][@qualifier='supportedLocale']) &gt; 1">
                                    <li id="ds-language-selection-xs" class="dropdown">
                                        <xsl:variable name="active-locale" select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='page'][@qualifier='currentLocale']"/>
                                        <button id="language-dropdown-toggle-xs" href="#" role="button" class="dropdown-toggle navbar-toggle hidden-lg hidden-md navbar-link" data-toggle="dropdown">
                                            <b class="visible-xs glyphicon glyphicon-globe" aria-hidden="true"/>
                                        </button>
                                        <ul class="dropdown-menu pull-right" role="menu" aria-labelledby="language-dropdown-toggle-xs" data-no-collapse="true">
                                            <xsl:for-each
                                                    select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='page'][@qualifier='supportedLocale']">
                                                <xsl:variable name="locale" select="."/>
                                                <li role="presentation">
                                                    <xsl:if test="$locale = $active-locale">
                                                        <xsl:attribute name="class">
                                                            <xsl:text>disabled</xsl:text>
                                                        </xsl:attribute>
                                                    </xsl:if>
                                                    <a>
                                                        <xsl:attribute name="href">
                                                            <xsl:value-of select="$current-uri"/>
                                                            <xsl:text>?locale-attribute=</xsl:text>
                                                            <xsl:value-of select="$locale"/>
                                                        </xsl:attribute>
                                                        <xsl:value-of
                                                                select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='supportedLocale'][@qualifier=$locale]"/>
                                                    </a>
                                                </li>
                                            </xsl:for-each>
                                        </ul>
                                    </li>
                                </xsl:if>


                            </ul>
                        </div>
                    </div>



                <div id="ds-search-option" class="ds-option-set pull-right">
                    <!-- The form, complete with a text box and a button, all built from attributes referenced
                 from under pageMeta. -->
                    <form id="ds-search-form" class="" method="post">
                        <xsl:attribute name="action">
                            <xsl:value-of select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='contextPath']"/>
                            <xsl:value-of
                                    select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='search'][@qualifier='simpleURL']"/>
                        </xsl:attribute>
                        <fieldset>
                            <div class="input-group">
                                <input class="ds-text-field form-control" type="text" placeholder="xmlui.general.search"
                                       i18n:attr="placeholder">
                                    <xsl:attribute name="name">
                                        <xsl:value-of
                                                select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='search'][@qualifier='queryField']"/>
                                    </xsl:attribute>
                                </input>
                                <span class="input-group-btn">
                                    <button class="ds-button-field btn btn-default" title="xmlui.general.go" i18n:attr="title">
                                        <span class="glyphicon glyphicon-search" aria-hidden="true"/>
                                        <xsl:attribute name="onclick">
                                                    <xsl:text>
                                                        var radio = document.getElementById(&quot;ds-search-form-scope-container&quot;);
                                                        if (radio != undefined &amp;&amp; radio.checked)
                                                        {
                                                        var form = document.getElementById(&quot;ds-search-form&quot;);
                                                        form.action=
                                                    </xsl:text>
                                            <xsl:text>&quot;</xsl:text>
                                            <xsl:value-of
                                                    select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='contextPath']"/>
                                            <xsl:text>/handle/&quot; + radio.value + &quot;</xsl:text>
                                            <xsl:value-of
                                                    select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='search'][@qualifier='simpleURL']"/>
                                            <xsl:text>&quot; ; </xsl:text>
                                                    <xsl:text>
                                                        }
                                                    </xsl:text>
                                        </xsl:attribute>
                                    </button>
                                </span>
                            </div>
                        </fieldset>
                    </form>
                </div>
                    </div>
                </div>
            </div>


        </header>

    </xsl:template>


    <!-- The header (distinct from the HTML head element) contains the title, subtitle, login box and various
        placeholders for header images -->
    <xsl:template name="buildTrail">
        <div class="trail-wrapper hidden-print">
            <div class="container">
                <div class="row">
                    <!--TODO-->
                    <div class="col-xs-10">
                        <xsl:choose>
                            <xsl:when test="count(/dri:document/dri:meta/dri:pageMeta/dri:trail) > 1">
                                <div class="breadcrumb dropdown visible-xs">
                                    <a id="trail-dropdown-toggle" href="#" role="button" class="dropdown-toggle"
                                       data-toggle="dropdown">
                                        <xsl:variable name="last-node"
                                                      select="/dri:document/dri:meta/dri:pageMeta/dri:trail[last()]"/>
                                        <xsl:choose>
                                            <xsl:when test="$last-node/i18n:*">
                                                <xsl:apply-templates select="$last-node/*"/>
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <xsl:apply-templates select="$last-node/text()"/>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                        <xsl:text>&#160;</xsl:text>
                                        <b class="caret"/>
                                    </a>
                                    <ul class="dropdown-menu" role="menu" aria-labelledby="trail-dropdown-toggle">
                                        <xsl:apply-templates select="/dri:document/dri:meta/dri:pageMeta/dri:trail"
                                                             mode="dropdown"/>
                                    </ul>
                                </div>
                                <ul class="breadcrumb hidden-xs">
                                    <xsl:apply-templates select="/dri:document/dri:meta/dri:pageMeta/dri:trail"/>
                                </ul>
                            </xsl:when>
                            <xsl:otherwise>
                                <ul class="breadcrumb">
                                    <xsl:apply-templates select="/dri:document/dri:meta/dri:pageMeta/dri:trail"/>
                                </ul>
                            </xsl:otherwise>
                        </xsl:choose>
                    </div>
                    <div class="col-xs-2 trail-toggle">
                    <button type="button" class="navbar-toggle hidden-lg hidden-md" data-toggle="offcanvas">
                        <span class="sr-only">
                            <i18n:text>xmlui.mirage2.page-structure.toggleNavigation</i18n:text>
                        </span>
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>

                    </button>
                    </div>
                </div>
            </div>
        </div>


    </xsl:template>

    <xsl:template match="dri:trail">
        <!--put an arrow between the parts of the trail-->
        <xsl:choose>
            <xsl:when test="position()=1">
                <i class="glyphicon glyphicon-home" aria-hidden="true"/>&#160;
            </xsl:when>
        </xsl:choose>

        <li>
            <xsl:attribute name="class">
                <xsl:text>ds-trail-link </xsl:text>
                <xsl:if test="position()=1">
                    <xsl:text>first-link </xsl:text>
                </xsl:if>
                <xsl:if test="position()=last()">
                    <xsl:text>last-link</xsl:text>
                </xsl:if>
            </xsl:attribute>
            <!-- Determine whether we are dealing with a link or plain text trail link -->
            <xsl:choose>
                <xsl:when test="./@target">
                    <a>
                        <xsl:variable name="target">
                            <xsl:choose>
                                <xsl:when test="contains(./@target, '{{context-path}}')">
                                    <xsl:call-template name="string-replace-all">
                                        <xsl:with-param name="text" select="./@target"/>
                                        <xsl:with-param name="replace" select="'{{context-path}}'"/>
                                        <xsl:with-param name="by" select="$context-path"/>
                                    </xsl:call-template>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:value-of select="./@target"/>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:variable>

                        <xsl:attribute name="href">
                            <xsl:value-of select="$target"/>
                        </xsl:attribute>
                        <xsl:apply-templates />
                    </a>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates />
                </xsl:otherwise>
            </xsl:choose>
        </li>
    </xsl:template>


    <xsl:template name="string-replace-all">
        <xsl:param name="text"/>
        <xsl:param name="replace"/>
        <xsl:param name="by"/>
        <xsl:choose>
            <xsl:when test="contains($text, $replace)">
                <xsl:value-of select="substring-before($text,$replace)"/>
                <xsl:value-of select="$by"/>
                <xsl:call-template name="string-replace-all">
                    <xsl:with-param name="text"
                                    select="substring-after($text,$replace)"/>
                    <xsl:with-param name="replace" select="$replace"/>
                    <xsl:with-param name="by" select="$by"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$text"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--The License-->
    <xsl:template name="cc-license">
        <xsl:param name="metadataURL"/>
        <xsl:variable name="externalMetadataURL">
            <xsl:text>cocoon:/</xsl:text>
            <xsl:value-of select="$metadataURL"/>
            <xsl:text>?sections=dmdSec,fileSec&amp;fileGrpTypes=THUMBNAIL</xsl:text>
        </xsl:variable>

        <xsl:variable name="ccLicenseName"
                      select="document($externalMetadataURL)//dim:field[@element='rights']"
                />
        <xsl:variable name="ccLicenseUri"
                      select="document($externalMetadataURL)//dim:field[@element='rights'][@qualifier='uri']"
                />
        <xsl:variable name="handleUri">
            <xsl:for-each select="document($externalMetadataURL)//dim:field[@element='identifier' and @qualifier='uri']">
                <a>
                    <xsl:attribute name="href">
                        <xsl:copy-of select="./node()"/>
                    </xsl:attribute>
                    <xsl:copy-of select="./node()"/>
                </a>
                <xsl:if test="count(following-sibling::dim:field[@element='identifier' and @qualifier='uri']) != 0">
                    <xsl:text>, </xsl:text>
                </xsl:if>
            </xsl:for-each>
        </xsl:variable>

        <xsl:if test="$ccLicenseName and $ccLicenseUri and contains($ccLicenseUri, 'creativecommons')">
            <div about="{$handleUri}" class="row">
                <div class="col-sm-3 col-xs-12">
                    <a rel="license"
                       href="{$ccLicenseUri}"
                       alt="{$ccLicenseName}"
                       title="{$ccLicenseName}"
                            >
                        <xsl:call-template name="cc-logo">
                            <xsl:with-param name="ccLicenseName" select="$ccLicenseName"/>
                            <xsl:with-param name="ccLicenseUri" select="$ccLicenseUri"/>
                        </xsl:call-template>
                    </a>
                </div> <div class="col-sm-8">
                <span>
                    <i18n:text>xmlui.dri2xhtml.METS-1.0.cc-license-text</i18n:text>
                    <xsl:value-of select="$ccLicenseName"/>
                </span>
            </div>
            </div>
        </xsl:if>
    </xsl:template>

    <xsl:template name="cc-logo">
        <xsl:param name="ccLicenseName"/>
        <xsl:param name="ccLicenseUri"/>
        <xsl:variable name="ccLogo">
            <xsl:choose>
                <xsl:when test="starts-with($ccLicenseUri,
                                           'http://creativecommons.org/licenses/by/')">
                    <xsl:value-of select="'cc-by.png'" />
                </xsl:when>
                <xsl:when test="starts-with($ccLicenseUri,
                                           'http://creativecommons.org/licenses/by-sa/')">
                    <xsl:value-of select="'cc-by-sa.png'" />
                </xsl:when>
                <xsl:when test="starts-with($ccLicenseUri,
                                           'http://creativecommons.org/licenses/by-nd/')">
                    <xsl:value-of select="'cc-by-nd.png'" />
                </xsl:when>
                <xsl:when test="starts-with($ccLicenseUri,
                                           'http://creativecommons.org/licenses/by-nc/')">
                    <xsl:value-of select="'cc-by-nc.png'" />
                </xsl:when>
                <xsl:when test="starts-with($ccLicenseUri,
                                           'http://creativecommons.org/licenses/by-nc-sa/')">
                    <xsl:value-of select="'cc-by-nc-sa.png'" />
                </xsl:when>
                <xsl:when test="starts-with($ccLicenseUri,
                                           'http://creativecommons.org/licenses/by-nc-nd/')">
                    <xsl:value-of select="'cc-by-nc-nd.png'" />
                </xsl:when>
                <xsl:when test="starts-with($ccLicenseUri,
                                           'http://creativecommons.org/publicdomain/zero/')">
                    <xsl:value-of select="'cc-zero.png'" />
                </xsl:when>
                <xsl:when test="starts-with($ccLicenseUri,
                                           'http://creativecommons.org/publicdomain/mark/')">
                    <xsl:value-of select="'cc-mark.png'" />
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="'cc-generic.png'" />
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <img class="img-responsive">
            <xsl:attribute name="src">
                <xsl:value-of select="concat($theme-path,'/images/creativecommons/', $ccLogo)"/>
            </xsl:attribute>
            <xsl:attribute name="alt">
                <xsl:value-of select="$ccLicenseName"/>
            </xsl:attribute>
        </img>
    </xsl:template>

    <!-- Like the header, the footer contains various miscellaneous text, links, and image placeholders -->
    <xsl:template name="buildFooter">
        <footer>
            <div class="row">
                <hr/>
                <div class="col-xs-7 col-sm-8 footer">

                    <div class="hidden-print footermargin">

                        <a>
                            <xsl:attribute name="href">
                                <xsl:value-of
                                        select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='contextPath'][not(@qualifier)]"/>
                                <xsl:text>/page/about</xsl:text>
                            </xsl:attribute>

                            <i18n:text>xmlui.dri2xhtml.structural.about-link</i18n:text>
                        </a>
                        <a>
                            <xsl:attribute name="href">
                                <xsl:value-of
                                        select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='contextPath'][not(@qualifier)]"/>
                                <xsl:text>/page/privacy</xsl:text>
                            </xsl:attribute>

                            <i18n:text>xmlui.dri2xhtml.structural.privacy-link</i18n:text>
                        </a>
                        <a>
                            <xsl:attribute name="href">
                                <xsl:value-of
                                        select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='contextPath'][not(@qualifier)]"/>
                                <xsl:text>/feedback</xsl:text>
                            </xsl:attribute>
                            <i18n:text>xmlui.dri2xhtml.structural.feedback-link</i18n:text>
                        </a>
                        <a href="https://github.com/ilri/DSpace" title="CGSpace source code on GitHub">
                            <span class="fa fa-github fa-2x" aria-hidden="true"></span>
                        </a>



                    </div>
                </div>

            </div>
            <!--Invisible link to HTML sitemap (for search engines) -->
            <a class="hidden">
                <xsl:attribute name="href">
                    <xsl:value-of
                            select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='contextPath'][not(@qualifier)]"/>
                    <xsl:text>/htmlmap</xsl:text>
                </xsl:attribute>
                <xsl:text>&#160;</xsl:text>
            </a>
        </footer>
    </xsl:template>


    <!--
            The meta, body, options elements; the three top-level elements in the schema
    -->




    <!--
        The template to handle the dri:body element. It simply creates the ds-body div and applies
        templates of the body's child elements (which consists entirely of dri:div tags).
    -->
    <xsl:template match="dri:body">
        <div>
            <xsl:if test="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='alert'][@qualifier='message']">
                <div class="alert">
                    <button type="button" class="close" data-dismiss="alert">&#215;</button>
                    <xsl:copy-of select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='alert'][@qualifier='message']/node()"/>
                </div>
            </xsl:if>

            <!-- Check for the custom pages -->
            <xsl:choose>
                <xsl:when test="starts-with($request-uri, 'page/about')">
                    <div class="hero-unit">
					<h2>About CGSpace</h2>
                       <p>CGSpace is a joint repository of several <a href="https://www.cgiar.org" title="CGIAR homepage">CGIAR</a> centers, research programs and partners' agricultural research outputs and knowledge products. It is a tool to archive, curate, disseminate and permanently preserve research outputs and information products. CGSpace is both a repository of open access content and a complete index of research outputs.</p>

                       <p>The collaboration is built across different initiatives with partners contributing to the core technical costs and working together to expand access to their products.</p>

                       <p>Note: Not all content is inside CGSpace; it links to much content on other platforms. All efforts have been made to provide high quality information. Links off the site are not the responsibility of CGSpace content partners and collaborators.</p>

					   <p>Please send feedback on any broken links or errors to us via the <a href="/feedback">Send Feedback</a> link below.</p>

					  <h2>Information for Developers</h2>
					  <p>CGSpace is built on <a href="http://www.dspace.org" title="DSpace homepage">DSpace</a>. It is interoperable with other repositories and supports content discovery and re-use through use of international Dublin Core Metadata standards as well as CGIAR-wide metadata standards.</p>

					    <p>The repository's metadata is exposed through both the Open Archives Initiative Protocol for Metadata Harvesting (OAI-PMH) and a REST API interface — <code>/oai</code> and <code>/rest</code>, respectively. For more information see the <a href="https://wiki.duraspace.org/display/DSDOC5x/DSpace+5.x+Documentation" title="DSpace wiki">DSpace documentation</a>.</p>

					    <p>Please try to exercise restraint when using these resources. For example, it is a great help to us if your programmatic use of the server can respect our <a href="/robots.txt"><code>robots.txt</code></a>, specify a user agent for its requests, and reuse its <code>JSESSIONID</code> cookie. Also note that we have a public test server at dspacetest.cgiar.org which is running a recent snapshot of the production CGSpace software and data — please use this if you're testing a new integration or harvesting process! Lastly, if you are using our data we would love to <a href="/feedback">hear from you</a>.</p>

					    <p>The CGSpace codebase is managed on <a href="https://github.com/ilri/DSpace">GitHub</a>.</p>

					  <h2>History and Evolution</h2>
                              <p>A little history and some credits.</p>

                              <p>CGSpace emerged from work by the <a href="https://www.ilri.org" title="ILRI homepage">International Livestock Research Institute (ILRI)</a> to make its products public in a state of the art repository. Starting in late 2009, ILRI set up a DSpace repository. Looking for ways to capture products of projects hosted by, but not belonging to ILRI, communities were set up for other initiatives, such as the CGIAR System-wide Livestock Program.</p>

								<p>In 2010 and 2011, the <a href="https://waterandfood.org" title="CGIAR Challenge Program on Water and Food homepage">CGIAR Challenge Program on Water and Food</a> and the <a href="https://ccafs.cgiar.org/" title="CGIAR Research Program on Climate Change, Agriculture and Food Security homepage">CGIAR Research Program on Climate Change, Agriculture and Food Security</a> joined this effort and agreed to work on a "co-tenant" application of a single DSpace.</p>

                               <p>With technical assistance and training from <a href="https://www.atmire.com" title="Atmire homepage">Atmire</a>, the collaboration has grown to include other centers and initiatives seeking to have such a repository while sharing costs and achieving synergies. Some of this work has been documented in a series of presentations and blogposts (<a href="http://www.slideshare.net/search/slideshow?searchfrom=header&amp;q=cgspace;">Slideshare</a> and <a href="https://maarifa.ilri.org/category/cgspace">Maarifa</a>).</p>

                              <p>The key individuals involved included:</p>
                              <ul>
                                <li>Peter Ballantyne (ILRI) ― instigated the repository, leads the overall effort.</li>
                                <li>Sisay Webshet (ILRI) ― set up the first ILRI DSpace, involved in all the technical developments.</li>
                                <li>Michael Victor (CPWF then WLE) ― saw the early opportunity to join forces.</li>
                                <li>Alan Orth (ILRI) ― moved DSpace to GNU/Linux and GitHub; troubleshoots and manages systems, upgrades, code, servers and more.</li>
                                <li>Bram Luyten (Atmire) ― confirmed the technical feasibility of a co-tenant application; provides ongoing state of the art advice and inputs and connections to the core DSpace developers.</li>
                                <li>Vanessa Meadu (CCAFS) ― joined forces and motivated DSpace to Drupal interface.</li>
                                <li>Abenet Yabowork (ILRI) ― curates and quality checks the ILRI content; supports partner content.</li>
                                <li>Tezira Lore (ILRI) ― from the beginning, she systematically published ILRI's food safety and zoonotic disease research through CGSpace.</li>
                                <li>Chris Addison (CTA) ― identified CGSpace as a suitable platform to host archive, and now also current, content from CTA.</li>
                                <li>Bizuwork Mulat, Abeba Desta and Goshu Cherinet (ILRI), Megan Zandstra and Leroy Mwanzia (CIAT), Udana Ariyawansa and Chandima Gunadasa (IWMI), Sufiet Erlita (CIFOR), Joel Ranck and Cecilia Ferreyra (CIP), Maria Garruccio (Bioversity), Martin Mueller (IITA), Ryan Miller (IFPRI), Thierry Lewyllie (CTA) and Daniel Haile-Michael and Tsega Tassema (ILRI web team) all brought their specific expertise and dedication to help move the collaboration forward.</li>
                              </ul>
					  <h2>Disclaimer</h2>
					    <p>CGSpace content providers and partners accept no liability to any consequence resulting from use of the content or data made available in this repository. Users of this content assume full responsibility for compliance with all relevant national or international regulations and legislation.</p>
                        
                    </div>
                </xsl:when>
                <xsl:when test="starts-with($request-uri, 'page/privacy')">
                    <div class="hero-unit">
                        <h2>CGSpace privacy statement (May 2018)</h2>
                        <p>The CGSpace platform is hosted by the International Livestock Research Institute (ILRI) on behalf of its partners. This statement aims to help you understand what information ILRI collects about you and how we use it. ILRI is committed to protecting your personal information. This statement is derived from the official ILRI privacy statement available at: <a href="https://hdl.handle.net/10568/92832">https://hdl.handle.net/10568/92832</a></p>
                        <h2>What personal information do we collect from CGSpace users?</h2>
                        <h3>Personal identification information</h3>
                        <p>When registering or logging into the CGSpace repository, you may be asked to enter your email address or other details, such as name and institutional affiliation. ILRI will collect your personal identification information only if you voluntarily submit such information to us. Users can always opt not to supply personal identification information, except that it may prevent them from engaging in certain activities, for example signing for email alerts.</p>
                        <h3>Non-personally identifiable information</h3>
                        <p>You can browse CGSpace without telling us who you are or revealing any personally identifiable information about yourself.</p>
                        <p>The only information we gather during general browsing is from standard <b>server logs</b>: these include your internet protocol (IP) address, browser type, operating system, and information such as the website that referred you to us, the files you download, the pages you visit, and the dates/times of those visits. These do not specifically identify you. The information is used only for website traffic analysis and is treated confidentially.</p>
                        <p><b>Cookie data</b>. The Site may use "cookies"; to enhance your user experience. A cookie is a small text file that a website saves on your computer or mobile device when you visit the site. There are multiple types of cookies, but cookies in general have two principal purposes:</p>
                        <ol>
                            <li>to improve your browsing experience by remembering your actions and preferences</li>
                            <li>to facilitate analysis of website traffic.</li>
                        </ol>
                        <p>ILRI uses cookies to facilitate the analysis of website traffic and to remember preferences you may have set. This helps us to understand and improve the performance and usability of CGSpace. Specifically, ILRI uses cookies when communicating with Google Analytics (for web traffic analysis). Personally identifiable information is not stored in these cookies.</p>
                        <h3>When do we collect personal information?</h3>
                        <p>You are not asked to provide any personally identifiable information to access most parts of CGSpace. You will be asked to provide basic personal information such as your email address to subscribe to email alerts or leave a comment on the Site.</p>
                        <h3>How does ILRI use your personal information?</h3>
                        <p>We will use your personally identifiable information for the purposes of:</p>
                        <ul>
                            <li>giving you the products, information or services you have requested</li>
                            <li>improving the quality of the products, information or services you have requested</li>
                            <li>communicating with you about an event or conference</li>
                            <li>evaluating your job application</li>
                            <li>complying with law and regulations</li>
                        </ul>
                        <p>To do some of this, we may process your information using third party service providers or agents who may be located outside your home country. However, your information will only be used for the purposes you requested or agreed to or as required by law. Please see section F on third party disclosure for more information on how we share your information with others.</p>
                        <p>We will use your non-personally identifiable information to facilitate analysis of website traffic to improve the performance, usability and data security of the Site.</p>
                        <h3>How does ILRI protect your personal information?</h3>
                        <p>ILRI adopts appropriate data collection, storage and processing practices and security measures to protect against unauthorized access, alteration, disclosure or destruction of your personal information and data stored on the Site and elsewhere.</p>
                        <h3>Third-party disclosure</h3>
                        <p>ILRI does not sell, trade, or rent user personal identification information to others. ILRI may share generic aggregated demographic information not linked to any personally identifiable information regarding visitors and users with our partners, trusted affiliates and advertisers for the purposes outlined above or as described in section G below.</p>
                        <p>We may also use third party service providers to help us with the management of offline and online services (e.g. the Site), such as sending out newsletters and undertaking surveys. We may share user information with these third parties for those limited purposes for which you have given your permission.</p>
                        <h3>Legal disclosures</h3>
                        <p>Notwithstanding anything to the contrary in this Privacy statement, users acknowledge, consent and agree that ILRI may disclose information in order to: (a) comply with applicable law, regulation, legal process, or governmental request; (b) protect the rights, property and safety of ILRI and others, including intellectual property rights; and (c) enforce or apply our agreements and policies.</p>
                        <p>If you post or send offensive, inappropriate, or objectionable content anywhere on or to the Site or otherwise engage in any disruptive behaviour on any ILRI service, we may use your personal information to stop such behaviour. Where ILRI reasonably believes that you are or may be in breach of any applicable laws (e.g. because content you have posted is considered defamatory or in violation of copyright), we may use your personal information to inform relevant third parties such as law enforcement agencies about the content and your behaviour.</p>
                        <h3>Third-party links</h3>
                        <p>You may find other content on CGSpace that link to the sites and services of our partners, donors and other third parties. ILRI does not control the content or links that appear on these sites and is not responsible for the practices employed by websites linked to or from the Site. Browsing and interaction on any other website, including websites which have a link to the Site, is subject to that website's own terms and policies. ILRI is, however, committed to the integrity of the Site and welcomes feedback on any of the linked sites.</p>
                        <p>ILRI also uses "social plugins" for Facebook, Google, LinkedIn, Flickr, Pinterest, SlideShare, YouTube and Twitter. The most common use of these social plugins is to share content on social networks. They also transmit cookies to and from the Site to a third party service.</p>
                        <h3>Children</h3>
                        <p>ILRI does not intend, and the Site is not designed, to collect personal information from children under the age of 18. If you are under 18 years old, you should not provide personal information on the Site or use it without the supervision or authorization of an adult.</p>
                        <h3>Specific data subject rights regarding data privacy and protection</h3>
                        <p>Privacy by design Privacy by design is a methodology that enables privacy to be "built in" to the design and architecture of information systems, business processes and networked infrastructure. ILRI ensures that all its archival systems containing personally identifiable information use design methodology or system procurement criteria that includes privacy by design.</p>
                        <h3>Collection of and access to personal data</h3>
                        <p>ILRI will only collect the minimum amount of personally identifiable data that is necessary to complete the action to which that information is associated. If actions change and information is no longer needed, we will stop collecting the information immediately.</p>
                        <p>Further, ILRI will only grant access to data to individuals who absolutely need access in order to perform their duties. If duties or individuals change, ILRI will remove permissions from any accounts who do not need access.</p>
                        <p>ILRI will also conduct periodic reviews of every filing system under its control and ensure that data collection and data access requirements are up to date. </p>
                        <h3>Affirmative consent</h3>
                        <p>In collecting your personal data, affirmative consent will be requested from you. The consent request notice contains the following information:</p>
                        <ul>
                            <li>ILRI contact details;</li>
                            <li>The reason for collecting the information;</li>
                            <li>Whether the information will be transferred to another country or international organization (e.g. the CGIAR System Organization);</li>
                            <li>How long the information will be stored;</li>
                            <li>How the data subject can correct, delete, restrict processing, or object to processing of their data as well as how they can receive their data to move it someplace else;</li>
                            <li>The right for the data subject to withdraw their consent at any time;</li>
                            <li>The right for the data subject to lodge a complaint with the appropriate authorities; and</li>
                            <li>If providing the personal data is a requirement to comply with a law or contract, the possible consequences of not providing the information.</li>
                        </ul>
                        <h3>Affirmative consent in signing up for ILRI surveys or information products</h3>
                        <p>In signing up to ILRI surveys or for our information products, the conditions and associated user rights are as follows:</p>
                        <ul>
                            <li>You may correct, delete or restrict processing of your data held by ILRI by writing to <a href="mailto:ILRIdataprivacysupport@cgiar.org">ILRIdataprivacysupport@cgiar.org</a>. We will respond within the time period specified in this privacy statement.</li>
                            <li>The information collected is for the purposes of providing you with the product requested and/or to improve the quality of our content.</li>
                            <li>Your information may be shared across ILRI and with partners participating in the respective projects, often in different countries.</li>
                            <li>The data provided to us through participation in ILRI surveys will be held for three years after which it will be destroyed.</li>
                            <li>The data provided to us by signing up for information products will be held for as long as you wish to receive the specific products.To remove yourself from the subscriber list, follow the instructions at the bottom of the email containing your information product.</li>
                            <li>Comments left by you on our blogs will be deleted upon your request to <a href="mailto:ILRIdataprivacysupport@cgiar.org">ILRIdataprivacysupport@cgiar.org</a>.</li>
                        </ul>
                        <h3>Data subject access rights</h3>
                        <p>You have the right to, upon request, access your information to amend and confirm accuracy; request your data be provided so you can submit it elsewhere; and request that your information be deleted from the ILRI data filing system.</p>
                        <ul>
                            <li>Upon request, ILRI will provide the data subject with their information free of charge unless the request is manifestly unfounded or excessive (particularly if it is repetitive). If unfounded or excessive then ILRI may charge a reasonable fee based on the administrative cost of providing the information;</li>
                            <li>ILRI will respond to you within one month of receipt of their request, and may extend the response period and must notify you within one month if so explaining why the extension is necessary, if the requests are complex or numerous. Unless the request is for a large amount of information, responses will not linger past three months of receipt of the request; and</li>
                            <li>ILRI will provide the requested information in an easily accessible, commonly used, electronic format.</li>
                        </ul>
                        <p>You can opt out of receiving emails from us at any time by unsubscribing to one of the Google FeedBurner subscriptions, look for the "unsubscribe now" link located at the bottom of the email you have signed up for. To unsubscribe from RSS updates, please check your specific reader's settings.</p>
                        <h3>Breach</h3>
                        <p>For data filing systems over which ILRI has control, a breach notification system and process is in place guaranteeing that data subjects will be notified of the breach within 72 hours (or less) of ILRI first having become aware of a breach. ILRI has robust mitigation and monitoring in place to prevent and/or identify a breach when it occurs.</p>
                        <h3>Third party data filing systems</h3>
                        <p>If data filing systems are hosted or managed by a third party, ILRI will use its best efforts and execute service agreements with appropriate compliance, confidentially and non-disclosure clauses.</p>
                        <h3>User acceptance of these terms</h3>
                        <p>By using the ILRI Site, you signify your acceptance of this statement, terms and conditions. If ILRI changes this privacy statement, we will post those changes to this page so that you are always aware of what information we collect and how we use it.</p>
                        <h3>Contacting ILRI</h3>
                        <p>For any questions regarding ILRI's Privacy statement, the practices of the Site or user's dealings with it, the contact information is as follows:</p>
                        <address>
International Livestock Research Institute (ILRI)<br />
Headquarters Nairobi Kenya P.O Box 30709-00100<br />
<a href="mailto:ILRIdataprivacysupport@cgiar.org">ILRIdataprivacysupport@cgiar.org</a>
                        </address>
                    </div>
                </xsl:when>
                <!-- Otherwise use default handling of body -->
                <xsl:otherwise>
                    <xsl:apply-templates />
                </xsl:otherwise>
            </xsl:choose>

        </div>
    </xsl:template>


    <!-- Currently the dri:meta element is not parsed directly. Instead, parts of it are referenced from inside
        other elements (like reference). The blank template below ends the execution of the meta branch -->
    <xsl:template match="dri:meta">
    </xsl:template>

    <!-- Meta's children: userMeta, pageMeta, objectMeta and repositoryMeta may or may not have templates of
        their own. This depends on the meta template implementation, which currently does not go this deep.
    <xsl:template match="dri:userMeta" />
    <xsl:template match="dri:pageMeta" />
    <xsl:template match="dri:objectMeta" />
    <xsl:template match="dri:repositoryMeta" />
    -->

    <xsl:template name="addJavascript">

        <!--TODO concat & minify!-->

        <xsl:element name="script">
            <xsl:text>if(!window.DSpace){window.DSpace={};}window.DSpace.context_path='</xsl:text><xsl:value-of select="$context-path"/><xsl:text>';window.DSpace.theme_path='</xsl:text><xsl:value-of select="$theme-path"/><xsl:text>';</xsl:text>
            <xsl:text>window.DSpace.config = window.DSpace.config || {};</xsl:text>
            <xsl:for-each select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='config' and @qualifier]">
                <xsl:text>window.DSpace.config['</xsl:text><xsl:value-of select="@qualifier"/><xsl:text>']='</xsl:text><xsl:value-of select="text()"/><xsl:text>';</xsl:text>
            </xsl:for-each>
        </xsl:element>


        <!--inject scripts.html containing all the theme specific javascript references
        that can be minified and concatinated in to a single file or separate and untouched
        depending on whether or not the developer maven profile was active-->
        <xsl:variable name="scriptURL">
            <xsl:text>cocoon://themes/</xsl:text>
            <!--we can't use $theme-path, because that contains the context path,
            and cocoon:// urls don't need the context path-->
            <xsl:value-of select="$pagemeta/dri:metadata[@element='theme'][@qualifier='path']"/>
            <xsl:text>scripts-dist.xml</xsl:text>
        </xsl:variable>
        <xsl:for-each select="document($scriptURL)/scripts/script">
            <script src="{$theme-path}{@src}">&#160;</script>
        </xsl:for-each>

        <!-- Add javascipt specified in DRI -->
        <xsl:for-each select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='javascript'][not(@qualifier)]">
            <script>
                <xsl:attribute name="src">
                    <xsl:value-of select="$theme-path"/>
                    <xsl:value-of select="."/>
                </xsl:attribute>&#160;</script>
        </xsl:for-each>

        <!-- add "shared" javascript from static, path is relative to webapp root-->
        <xsl:for-each select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='javascript'][@qualifier='static']">
            <!--This is a dirty way of keeping the scriptaculous stuff from choice-support
            out of our theme without modifying the administrative and submission sitemaps.
            This is obviously not ideal, but adding those scripts in those sitemaps is far
            from ideal as well-->
            <xsl:choose>
                <xsl:when test="text() = 'static/js/choice-support.js'">
                    <script>
                        <xsl:attribute name="src">
                            <xsl:value-of select="$theme-path"/>
                            <xsl:text>js/choice-support.js</xsl:text>
                        </xsl:attribute>&#160;</script>
                </xsl:when>
                <xsl:when test="not(starts-with(text(), 'static/js/scriptaculous'))">
                    <script>
                        <xsl:attribute name="src">
                            <xsl:value-of
                                    select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='contextPath'][not(@qualifier)]"/>
                            <xsl:text>/</xsl:text>
                            <xsl:value-of select="."/>
                        </xsl:attribute>&#160;</script>
                </xsl:when>
            </xsl:choose>
        </xsl:for-each>


        <script>
            <xsl:attribute name="src">
                <xsl:value-of select="$theme-path"/>
                <xsl:text>scripts/cua-overrides.js</xsl:text>
            </xsl:attribute>
            &#160;
        </script>

        <!-- add setup JS code if this is a choices lookup page -->
        <xsl:if test="dri:body/dri:div[@n='lookup']">
            <xsl:call-template name="choiceLookupPopUpSetup"/>
        </xsl:if>

        <!-- add Google Analytics -->
        <xsl:call-template name="googleAnalytics"/>

    </xsl:template>

    <!--The Language Selection-->
    <xsl:template name="languageSelection">
        <xsl:if test="count(/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='page'][@qualifier='supportedLocale']) &gt; 1">
            <li id="ds-language-selection" class="dropdown">
                <xsl:variable name="active-locale" select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='page'][@qualifier='currentLocale']"/>
                <a id="language-dropdown-toggle" href="#" role="button" class="dropdown-toggle" data-toggle="dropdown">
                    <span class="hidden-xs">
                        <xsl:value-of
                                select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='supportedLocale'][@qualifier=$active-locale]"/>
                        <xsl:text>&#160;</xsl:text>
                        <b class="caret"/>
                    </span>
                </a>
                <ul class="dropdown-menu pull-right" role="menu" aria-labelledby="language-dropdown-toggle" data-no-collapse="true">
                    <xsl:for-each
                            select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='page'][@qualifier='supportedLocale']">
                        <xsl:variable name="locale" select="."/>
                        <li role="presentation">
                            <xsl:if test="$locale = $active-locale">
                                <xsl:attribute name="class">
                                    <xsl:text>disabled</xsl:text>
                                </xsl:attribute>
                            </xsl:if>
                            <a>
                                <xsl:attribute name="href">
                                    <xsl:value-of select="$current-uri"/>
                                    <xsl:text>?locale-attribute=</xsl:text>
                                    <xsl:value-of select="$locale"/>
                                </xsl:attribute>
                                <xsl:value-of
                                        select="/dri:document/dri:meta/dri:pageMeta/dri:metadata[@element='supportedLocale'][@qualifier=$locale]"/>
                            </a>
                        </li>
                    </xsl:for-each>
                </ul>
            </li>
        </xsl:if>
    </xsl:template>


    <xsl:template match="dri:trail" mode="dropdown">
        <!--put an arrow between the parts of the trail-->
        <li role="presentation">
            <!-- Determine whether we are dealing with a link or plain text trail link -->
            <xsl:choose>
                <xsl:when test="./@target">
                    <a role="menuitem">
                        <xsl:attribute name="href">
                            <xsl:value-of select="./@target"/>
                        </xsl:attribute>
                        <xsl:if test="position()=1">
                            <i class="glyphicon glyphicon-home" aria-hidden="true"/>&#160;
                        </xsl:if>
                        <xsl:apply-templates />
                    </a>
                </xsl:when>
                <xsl:when test="position() > 1 and position() = last()">
                    <xsl:attribute name="class">disabled</xsl:attribute>
                    <a role="menuitem" href="#">
                        <xsl:apply-templates />
                    </a>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:attribute name="class">active</xsl:attribute>
                    <xsl:if test="position()=1">
                        <i class="glyphicon glyphicon-home" aria-hidden="true"/>&#160;
                    </xsl:if>
                    <xsl:apply-templates />
                </xsl:otherwise>
            </xsl:choose>
        </li>
    </xsl:template>


</xsl:stylesheet>
