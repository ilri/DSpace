(function ($) {
    window.atmire = window.atmire || {};
    window.atmire.CUA = window.atmire.CUA || {};
    window.atmire.CUA.statlet = window.atmire.CUA.statlet || {};
    var afterLoadAdditionsCallbacks = atmire.CUA.statlet.afterLoadAdditionsCallbacks = atmire.CUA.statlet.afterLoadAdditionsCallbacks || [];
    afterLoadAdditionsCallbacks.push(override);

    var cuaTemplates = ["bar", "pie"];
    var templateMapper = {
        bar: "bar",
        distributed_bar: "distributed_bar",
        line: "bar",
        donut: "pie",
        pie: "pie",
        line_downloads: "bar",
        bar_countries: "distributed_bar"
    };


    function setSeriesClassNames(statlet, seriesNames) {
        var data = statlet.chartist[atmire.CUA.getViewPort()];

        for (var i = 0; i < data.series.length && i < seriesNames.length; i++) {
            var serie = data.series[i];
            data.series[i] = {
                value: serie,
                className: 'ct-series-' + seriesNames[i]
            };

            statlet.labels[i].charIndex = seriesNames[i];
        }
    }

    function override() {

        var cua = atmire.CUA = atmire.CUA || {};
        var statletNS = atmire.CUA.statlet;
        var viewports = statletNS.constants.viewports;

        // overriding a function originally defined in aspects/ReportingSuite/statlet/charts/chartist.js
        statletNS.template = statletNS.template || {};
        statletNS.template.graph = function (statlet) {

            var templateName, templateFunction;
            var type = (statlet.render.default && statlet.render.default['graph-type']) || "bar";
            if (cuaTemplates.indexOf(templateMapper[type]) < 0) {
                templateName = 'statlet_' + templateMapper[type];
                templateFunction = DSpace.getTemplate(templateName);
            } else {
                templateName = 'statlet/graphs/chartist/' + templateMapper[type];
                templateFunction = atmire.CUA.getTemplate(templateName);
            }
            return templateFunction(statlet);
        };


        // aspects/ReportingSuite/statlet/charts/chartist/pie.js
        var originalPrePie = statletNS.chartist.pre.pie;
        statletNS.chartist.pre.pie = function (statlet) {
            originalPrePie(statlet);

            var seriesNames = ['downloads', 'abstracts'];
            setSeriesClassNames(statlet, seriesNames);
        };

        // aspects/ReportingSuite/statlet/charts/chartist/bar.js
        statletNS.chartist.pre.distributed_bar = function (statlet) {
            var data, i, j, cell, row, serie_row, size;
            statlet.chartist = {};
            statlet.classes = [];
            for (size in viewports) {
                if (viewports.hasOwnProperty(size)) {
                    data = statlet.chartist[size] = {};

                    var max = statlet.renderMatrix[0].length - 1;
                    var rendering = statlet._render;
                    if (rendering.hasOwnProperty(size) && rendering[size]['max-columns']) {
                        max = parseInt(rendering[size]['max-columns']);
                    }
                    data.key = max;
                    data.labels = statlet.labels;
                    data.series = [];
                    //data.series[0] = [];

                    var hasData = false;
                    for (i = 1; i < statlet.renderMatrix.length; i++) {
                        row = statlet.renderMatrix[i];
                        j = (statlet.renderMatrix[0].length) - max;
                        //serie_row = data.series[i-1] = [];
                        //serie_row = data.series[i];
                        serie_row = data.series;
                        while (j < row.length) {
                            serie_row.push(row[j].value);
                            if (row[j].value !== 0) {
                                hasData = true;
                            }
                            j++
                        }
                    }
                    if (!hasData) {
                        statlet.classes.push('hidden-' + size);
                    }
                }
            }
        };

        // aspects/ReportingSuite/statlet/charts/chartist/bar.js
        statletNS.chartist.post.distributed_bar = function (statlet, content, callback) {
            var chartist;
            var element = $('.ct-chart', content).get(0);
            var $content = $('.statlet', content);
            var $element = $(element);
            var classes = $element.attr('class');

            var seriesBarDistance_xs = 0;
            var seriesBarDistance_sm = 0;
            var bar_width_xs = 0;
            var bar_width_sm = 0;
            var magic_nb_sm = 540;
            var magic_nb_sx = 235;

            var supported_width = [1, 5, 10, 15, 20, 25];

            var xs_data = statlet.chartist['xs'];
            var cols = xs_data.labels.length;
            var rows = xs_data.series.length;
            bar_width_xs = (magic_nb_sx / cols) / rows;
            for (var i = supported_width.length - 1; i > 0; i--) {
                if (supported_width[i] <= bar_width_xs || (supported_width[i] - bar_width_xs) < 5) {
                    seriesBarDistance_xs = supported_width[i] - (supported_width[i] - bar_width_xs);
                    bar_width_xs = supported_width[i];
                    if (seriesBarDistance_xs < 2) {
                        seriesBarDistance_xs = 1;
                    }
                    break;
                }
            }

            var sm_data = statlet.chartist['sm'];
            cols = sm_data.labels.length;
            rows = sm_data.series.length;
            bar_width_sm = (magic_nb_sm / cols) / rows;
            for (var i = supported_width.length - 1; i > 0; i--) {
                if (supported_width[i] <= bar_width_sm || (supported_width[i] - bar_width_sm) < 5) {
                    seriesBarDistance_sm = supported_width[i] - (supported_width[i] - bar_width_sm);
                    bar_width_sm = supported_width[i];
                    if (seriesBarDistance_sm < 2) {
                        seriesBarDistance_sm = 1;
                    }
                    break;
                }
            }

            var sm_y_offset = Math.max(statletNS.chartist.getHighestValue(statlet, 'sm').toString().length * 10, 30);
            var xs_y_offset = Math.max(statletNS.chartist.getHighestValue(statlet, 'xs').toString().length * 10, 30);

            statlet.type = "number";

            var options = {
                seriesBarDistance: 15,
                axisY: {
                    labelInterpolationFnc: function (value) {
                        return statletNS.chartist.labelInterpolationFncAxisY(value, statlet);
                    },
                    showGrid: true
                },
                axisX: {
                    showGrid: true
                },
                classNames: {bar: 'ct-bar ct-bar'},
                distributeSeries: true,
                chartPadding: {
                    left: 50,
                    right: 25,
                    top: 25,
                    bottom: 10
                }
            };

            var responsiveOptions = [
                ['screen and (min-width: ' + (statletNS.constants.viewports.sm) + 'px)', {
                    seriesBarDistance: seriesBarDistance_sm,
                    axisX: {
                        labelInterpolationFnc: function (cell) {
                            return statletNS.chartist.labelInterpolationFncAxisX(cell, 'lg')
                        }
                    },
                    axisY: {offset: sm_y_offset},
                    classNames: {bar: 'ct-bar ct-bar-sm-' + bar_width_sm},
                    distributeSeries: true

                }],
                ['screen and (max-width: ' + (statletNS.constants.viewports.sm - 1) + 'px)', {
                    seriesBarDistance: seriesBarDistance_xs,
                    axisX: {
                        labelInterpolationFnc: function (cell) {
                            return statletNS.chartist.labelInterpolationFncAxisX(cell, 'xs')
                        }
                    },
                    axisY: {offset: xs_y_offset},
                    classNames: {bar: 'ct-bar ct-bar-xs-' + bar_width_xs},
                    distributeSeries: true
                }]
            ];

            if (cua.isXsViewport()) {
                $element.addClass('ct-perfect-fifth');
            } else {
                $element.addClass('ct-double-octave');
            }

            var barData = statlet.chartist[cua.getViewPort()];

            chartist = new Chartist.Bar(element, barData, options, responsiveOptions);

            statletNS.chartist.initToolTip($content, $element, statlet, '.ct-bar', false);

            window.addEventListener('resize', function () {
                var data = statlet.chartist[cua.getViewPort()];
                $element.removeClass();
                $element.addClass(classes);
                if (cua.isXsViewport()) {
                    $element.addClass('ct-perfect-fifth');
                } else {
                    $element.addClass('ct-double-octave');
                }
                if (data.key !== chartist.data.key) {
                    chartist.update(data);
                }
            });

            chartist.on('created', function () {
                if ($.isFunction(callback)) {
                    callback();
                }
            });


            return chartist;

        }


        statletNS.chartist.pre.line_downloads = function (statlet) {
            statletNS.chartist.pre.line(statlet);
            var seriesNames = ['abstracts'];
            setSeriesClassNames(statlet, seriesNames);
        };

        statletNS.chartist.post.line_downloads = function (statlet, content, callback) {
            statletNS.chartist.post.line(statlet, content, callback);
        };

        statletNS.chartist.pre.bar_countries = function (statlet) {
            statletNS.chartist.pre.distributed_bar(statlet);

            for (var size in viewports) {
                if (viewports.hasOwnProperty(size)) {
                    statlet.chartist[size].labels = statlet.labels;
                }
            }

            var seriesNames = [];
            var dataLength = statlet.chartist[atmire.CUA.getViewPort()].series.length;
            for (var i = 0; i < dataLength; i++){
                seriesNames.push('abstracts');
            }
            setSeriesClassNames(statlet, seriesNames);
        };

        statletNS.chartist.post.bar_countries = function (statlet, content, callback) {
            statletNS.chartist.post.distributed_bar(statlet, content, callback);
        };

    }

})(jQuery);

