# Pollmaster V 2.5

## Overview

This bot is a fork of the original poll bot. The aim of this one is to provide a boardgamers association poll.
This poll is not designed to show which option is more liked but who want to play what game.

Here is a quick list of features:

- Create a poll to know who is want to play what game
- Refresh your poll for the next week
- Schedule a poll so that it is shown every week (on dev)
- Remove a poll
- Show all polls

## The most important commands

| Command                | Effect                                             |
|------------------------|----------------------------------------------------|
| pm!help                | Shows an interactive help menu                     |
| pm!cmd                 | Create a new poll                                  |
| pm!restart <label>     | Restart a poll                                     |
| pm!show <label>        | Show a poll                                        |
| pm!schedule <label>    | Schedule a poll each week                          |
| pm!stats               | Print the stats for past polls                     |

## Old poll commands (use with care)

| Command                | Effect                                             |
|------------------------|----------------------------------------------------|
| pm!help                | Shows an interactive help menu                     |
| pm!new                 | Starts a new poll with the most common settings    |
| pm!advanced            | Starts a new poll all the settings                 |
| pm!quick               | Starts a new poll with just a question and options |
| pm!show <label>        | Shows poll in a specified channel (can be different from original channel) |
| pm!prefix <new prefix> | Change the prefix for this server                  |
| @mention prefix        | Show the prefix if you forgot it                   |
| pm!userrole <any role> | Set the role that has the rights to use the bot    |

## Examples

```
# Create a standard poll
pm!cmd -q "A quoi voulez vous jouer mercredi ?" -o "Present avec les clés, ADG, Bataille empire, Bolt, Frostgrave, Game of throne, Guildball, Khârn-ages, Malifaux, Saga ADM, Saga histo, SW Armada, Autres, Absent" -l "mercredi" -mc "5"

# Restart a poll
pm!restart <label>

# Show the poll again without clearing people
pm!show <label>

# Automatically restart a poll each week (at the time it has been shceduled)
pm!schedule <label>
```

## Getting Started

Users with the server permission "Manage Server" will have all rights from the start, meaning you can get started with pm!new right away!

To grant users without "Manage Server" poll creation access to the bot, create and distribute the role *polladmin* or *polluser*. If you already have roles for these rights you can tell the bot by typing *pm!adminrole <your role>* and *pm!userrole <your role>*.

