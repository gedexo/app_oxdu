(function () {
    "use strict";
    document.querySelectorAll(".custom-controls-stacked input").forEach((ele)=>{
        ele.onclick = ()=>{
            console.log(ele.value)
            if(ele.value == "option2"){
                document.querySelector(".enable-smtpemail").classList.remove("d-none")
            }else{
                document.querySelector(".enable-smtpemail").classList.add("d-none")
            }
        }
    })

    document.querySelector("#switch-md").onclick = (ele)=>{
        if(document.querySelector("#switch-md").checked){
            document.querySelector(".open-paypal").classList.add("d-block")
            document.querySelector(".open-paypal").classList.remove("d-none")
        }else{
            document.querySelector(".open-paypal").classList.add("d-none")
            document.querySelector(".open-paypal").classList.remove("d-block")
        }
    }

})();
