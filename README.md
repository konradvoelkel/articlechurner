articlechurner
==============

A lightweight article management system based on random re-evaluation and cumulative note-taking.

Intended for keeping track of scientific publications, in particular using ArXiV and MathSciNet.

Implemented as webservice in Python+HTML+CSS+JS with a single human-readable CSV file as "database".

There are several known bugs at the moment. It is not recommended to run the webservice with public access anywhere, as user input is not sanitized in any way.

A "better" solution to article management using the approach developed here might be to take an existing article management software such as Mendeley, JabRef, etc. and add (via a plug-in) the ability to take cumulative notes and to get random re-evaluation. However, not building upon an existing software has the advantage of preventing vendor lock-in.

If anyone intends to use this, please don't hesitate to write the developer an email.
