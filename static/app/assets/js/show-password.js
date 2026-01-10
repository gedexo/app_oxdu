"use strict"

// for show password 
let createpassword = (type, ele) => {
    document.getElementById(type).type = document.getElementById(type).type == "password" ? "text" : "password"
    let icon = ele.childNodes[0].classList
    let stringIcon = icon.toString()
    if (stringIcon.includes("fe-eye-off")) {
        ele.childNodes[0].classList.remove("fe-eye-off")
        ele.childNodes[0].classList.add("fe-eye")
    }
    else {
        ele.childNodes[0].classList.remove("fe-eye")
        ele.childNodes[0].classList.add("fe-eye-off")
    }
}