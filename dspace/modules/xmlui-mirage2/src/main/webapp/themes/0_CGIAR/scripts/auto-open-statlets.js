(function ($) {
    window.DSpace = window.DSpace || {};
    window.DSpace.config = window.DSpace.config || {};
    window.atmire = window.atmire || {};
    window.atmire.CUA = window.atmire.CUA || {};
    window.atmire.CUA.statlet = window.atmire.CUA.statlet || {};

    if (window.DSpace.config['atmire-cua.auto-open-statlets'] === 'true') {
        var afterInitCallbacks = window.atmire.CUA.statlet.afterInitCallbacks = window.atmire.CUA.statlet.afterInitCallbacks || [];
        $(function () {
            afterInitCallbacks.push(function () {
                var statsWrapper = $('#aspect_statistics_StatletTransformer_div_statswrapper');
                if (statsWrapper.length === 0 || statsWrapper.is(':hidden')) {
                    $('#aspect_statistics_StatletTransformer_div_showStats').find('.btn').click();
                }
            });
        });
    }
})(jQuery);