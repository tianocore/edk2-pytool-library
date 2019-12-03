# Build Objects

## What are they?

Build Objects are classes that hold the instructions for the edk2 build framework.
The central class is the `recipe`.
This holds all the components that need to be built and their respective library classes.
In the future, it will also contain the flash map information.

We've written a parser for DSC's to convert them into recipes. 
In the future, we hope to include FDF's as well.

## Who are they for?

Build objects are for anyone dealing with complex and large projects.
In projects, more and more DSC's are taking advantage of the !include functionality. However, there are a few problems with that fact. 
1. DSC's are fragile
2. Includes have no idea what is already in your file. An include might expect you to be in a defines section. You have no way to know this from the main DSC file.
3. 

## Why were they made?

To better abstract away the essense of what a build is doing. DSC is a way to communicate a recipe. 

## How are they being used?

DSC compositing/transformations