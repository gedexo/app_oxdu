(function () {
    "use strict";

    var myElement1 = document.getElementById('ChatBody');
    new SimpleBar(myElement1, { autoHide: true });

    var myElement2 = document.getElementById('ChatList');
    new SimpleBar(myElement2, { autoHide: true });

})();
