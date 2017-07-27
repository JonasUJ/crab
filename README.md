# Introduction
It's called Crab because it can be confused with crap. Why you'd ever use this for anything is beyond my comprehension, but here it is nonetheless.
This started as a console replica, but as with the Windows console, you can create .bat files which will execute a bunch of commands automatically. I soon realized that this could become some sort of language, but it didn't quite work as i wanted it to, so i started anew and abandon the old project: https://github.com/JonasUJ/console

# Crab
The new project is a bunch of methods and a parser that calls the methods. The keyword `cal` has a specific method `do_cal` which is called when the parser finds a `cal` in the code. The methods also get some arguments, ofcourse, `cal 2 * 4` calls `do_cal` with the arguments `2`, `*` and `4`. `do_cal` then does something and returns a value, the value is then directly placed in the code and the parser moves on.

This means that this:
```
cal 1 + 2 * 3
```
Becomes:
```
7
```
Which isn't very useful since we don't do anything with the 7, just put it in the code until the program finishes executing.

# Embeds
This is where embeds come in, they let you have multiple commands on one line. 
They work by basically replacing the embed with the returned value and thereby creating a new command. We can use this to output the 7:
```
cout {cal 1 + 2 * 3}
```
Will become:
```
cout 7
```
Which doesn't return anything, but `cout` outputs its arguments to the console. You can also have embeds inside other embeds:
```
cout {cal 5 * {cal 5 - 3}}
```
This outputs 10.
Embedded embeds are executed recursivly from back to front inside out, if that makes sense. Here the are labelled 1-6 in order of execution:
```
6 {5 {3 {2} {1}} {4}}
```

# Documentation
For documentation on what commands exists and how keywords behave take a look in the examples folder https://github.com/JonasUJ/crab/examples
