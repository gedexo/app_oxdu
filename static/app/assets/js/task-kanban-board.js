(function () {
    "use strict"

    dragula([ document.querySelector('#onprogress-draggable'), document.querySelector('#inprogress-tasks-draggable'), document.querySelector('#onhold-tasks-draggable'), document.querySelector('#completed-tasks-draggable')]);


    var myElement3 = document.getElementById('inprogress-tasks');
    new SimpleBar(myElement3, { autoHide: true });

    var myElement4 = document.getElementById('onhold-tasks');
    new SimpleBar(myElement4, { autoHide: true });

    var myElement2 = document.getElementById('onprogress-tasks');
    new SimpleBar(myElement2, { autoHide: true });

    var myElement5 = document.getElementById('completed-tasks');
    new SimpleBar(myElement5, { autoHide: true });


    document.addEventListener("DOMContentLoaded", () => {
        setInterval(() => {
            let i = [
                document.querySelector('#onprogress-draggable'),
                document.querySelector('#inprogress-tasks-draggable'),
                document.querySelector('#onhold-tasks-draggable'),
                document.querySelector('#completed-tasks-draggable')

            ]
            i.map((ele) => {
                if (ele) {
                    if (ele.children.length == 0) {
                        ele.classList.add("task-Null")
                        document.querySelector(`#${ele.getAttribute("data-view-btn")}`).nextElementSibling.classList.add("d-none")
                    }
                    if (ele.children.length != 0) {
                        ele.classList.remove("task-Null")
                        document.querySelector(`#${ele.getAttribute("data-view-btn")}`).nextElementSibling.classList.remove("d-none")
                    }
                }
            })
        }, 100);
    })

})();