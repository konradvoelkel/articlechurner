// ==UserScript==
// @name          ImportMathSciNettoArticleChurner
// @namespace     http://pkm.konradvoelkel.com
// @version       0.1
// @description   Have a button to quick-import into AC running on localhost:8000
// @include       http://www.ams.org/mathscinet*
// @include       http://www.ams.org/mathscinet/*
// @copyright  2014+, Konrad Voelkel
// ==/UserScript==

var appuri = "localhost:8000";

var headlinediv = document.getElementById("content").children[4].children[1];

var title = headlinediv.querySelectorAll(".title")[0].textContent;
var authors = headlinediv.children[3].textContent;
var mrlink = headlinediv.querySelectorAll(".headlineMenu")[0].children[4].getAttribute('href', 2);
title = title.replace(/(\r\n|\n|\r)/gm,"");

var actitle = authors + ": " + title;
var acuri = mrlink; //document.URL;

var formstyle = "float:left; padding-right:1em; margin:1ex;";
var buttonstyle = "font-size:120%; height:4ex; width:19em;";

var acform = "<form action=\"http://" + appuri + "/edit/\" method=\"post\" style=\"" + formstyle + "\">" +
    "<input name=\"uri\" id=\"uri\" type=\"hidden\" value=\"" + acuri + "\">" +
    "<input name=\"title\" id=\"title\" type=\"hidden\" value=\"" + actitle + "\">" +
    "<input name=\"oldnotes\" value=\"\" type=\"hidden\">" +
    "<input name=\"newnotes\" value=\"\" type=\"hidden\">" +
    "<input id=\"rating\" name=\"rating\" value=\"9\" type=\"hidden\">" +
    "<input type=\"submit\" id=\"submit\" value=\"Submit to ArticleChurner\" style=\"" + buttonstyle + "\">" +
  "</form>";

var accontainer = document.createElement("p");
accontainer.innerHTML = acform;

headlinediv.children[0].appendChild(accontainer);