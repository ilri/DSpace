// Initialize cookieconsent popup
// See: https://github.com/insites/cookieconsent
function initializeCookieConsent() {
    window.cookieconsent.initialise({
        "position": "bottom",
        "type": "opt-in",
        "content": {
            "message": "This site uses cookies. By clicking \"agree\" and continuing to use this site you agree to our use of cookies.",
            "dismiss": "Disagree",
            "allow": "Agree",
            "link": "Our privacy statement.",
            "href": "https://cgspace.cgiar.org/page/privacy"
        }
    });
};

// Quick function to check cookie status
// From: https://www.w3schools.com/js/js_cookies.asp
function getCookie(cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for(var i = 0; i <ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}
