// ==UserScript==
// @name          ImportArXiVtoArticleChurner
// @namespace     http://pkm.konradvoelkel.com
// @version       0.1
// @description   Have a button to quick-import into AC running on localhost:8000
// @include       http://arxiv.org/abs/*
// @include       http://www.arxiv.org/abs/*
// @copyright  2014+, Konrad Voelkel
// ==/UserScript==

var appuri = "localhost:8000";

var leftcolumn = document.getElementById("abs").children[1];
var titleh1 = leftcolumn.children[1];
var title = titleh1.childNodes[1].textContent;
var authors = leftcolumn.children[2].children[1].textContent;
title = title.replace(/(\r\n|\n|\r)/gm,"");

var actitle = authors + ": " + title;
var acuri = document.URL;

var formstyle = "float:left; padding-right:1em; margin:1ex;";
var buttonstyle = "font-size:140%; height:4ex; width:12em;";

var acform = "<form action=\"http://" + appuri + "/edit/\" method=\"post\" style=\"" + formstyle + "\">" +
    "<input name=\"uri\" id=\"uri\" type=\"hidden\" value=\"" + acuri + "\">" +
    "<input name=\"title\" id=\"title\" type=\"hidden\" value=\"" + actitle + "\">" +
    "<input name=\"oldnotes\" value=\"\" type=\"hidden\">" +
    "<input name=\"newnotes\" value=\"\" type=\"hidden\">" +
    "<input id=\"rating\" name=\"rating\" value=\"9\" type=\"hidden\">" +
    "<input type=\"submit\" id=\"submit\" value=\"Submit to ArticleChurner\" style=\"" + buttonstyle + "\">" +
  "</form>";

var accontainer = document.createElement("span");
accontainer.innerHTML = acform;

titleh1.appendChild(accontainer);