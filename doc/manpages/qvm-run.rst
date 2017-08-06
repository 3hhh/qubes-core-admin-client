.. program:: qvm-run

:program:`qvm-run` -- Run a command in a specified VM
=====================================================

Synopsis
--------

:command:`qvm-run` [options] *VMNAME* *COMMAND*
:command:`qvm-run` [options] --all [--exclude *EXCLUDE*]  *COMMAND*
:command:`qvm-run` [options] --dispvm [*BASE_APPVM*] *COMMAND*

Options
-------

.. option:: --help, -h

   Show the help message and exit.

.. option:: --verbose, -v

   Increase verbosity.

.. option:: --quiet, -q

   Decrease verbosity.

.. option:: --all

   Run the command on all qubes. You can use :option:`--exclude` to limit the
   qubes set. Command is never run on the dom0.

.. option:: --exclude

   Exclude the qube from :option:`--all`.

.. option:: --dispvm [BASE_APPVM]

   Run the command fresh DisposableVM created out of *BASE_APPVM*. This option
   is mutually exclusive with *VMNAME*, --all and --exclude.

.. option:: --user=USER, -u USER

   Run command in a qube as *USER*.

.. option:: --auto, --autostart, -a

   Ignored. Qube is autostarted by default.

.. option:: --no-auto, --no-autostart, -n

   Do not start the qube automatically, fail the operation if not running.

.. option:: --pass-io, -p

   Pass standard input and output to and from the remote program.

.. option:: --localcmd=COMMAND

   With :option:`--pass-io`, pass standard input and output to and from the
   given program.

.. option:: --gui

   Run the command with GUI forwarding enabled, which is the default. This
   switch can be used to counter :option:`--no-gui`.

.. option:: --no-gui, --nogui

   Run the command without GUI forwarding enabled. Can be switched back with
   :option:`--gui`.

.. option:: --service

   Start RPC service instead of shell command. Specify name of the service in
   place of *COMMAND* argument. You can also specify service argument, appending
   it to the service name after `+` character.

.. option:: --colour-output=COLOUR, --color-output=COLOR

   Mark the qube output with given ANSI colour (ie. "31" for red). The exact
   mapping of numbers to colours and styles depends of the particular terminal
   emulator.

   Colouring can be disabled with :option:`--no-colour-output`.

.. option:: --colour-stderr=COLOUR, --color-stderr=COLOR

   Mark the qube stderr with given ANSI colour (ie. "31" for red). The exact
   mapping of numbers to colours and styles depends of the particular terminal
   emulator.

   Colouring can be disabled with :option:`--no-colour-stderr`.

.. option:: --no-colour-output, --no-color-output

   Disable colouring the stdout.

.. option:: --no-colour-stderr, --no-color-stderr

   Disable colouring the stderr.

.. option:: --filter-escape-chars

   Filter terminal escape sequences (default if output is terminal).
   
   Terminal control characters are a security issue, which in worst case amount
   to arbitrary command execution. In the simplest case this requires two often
   found codes: terminal title setting (which puts arbitrary string in the
   window title) and title repo reporting (which puts that string on the shell's
   standard input.

.. option:: --no-filter-escape-chars

   Do not filter terminal escape sequences. This is DANGEROUS when output is
   a terminal emulator. See :option:`--filter-escape-chars` for explanation.

Authors
-------

| Joanna Rutkowska <joanna at invisiblethingslab dot com>
| Rafal Wojtczuk <rafal at invisiblethingslab dot com>
| Marek Marczykowski <marmarek at invisiblethingslab dot com>
| Wojtek Porczyk <woju at invisiblethingslab dot com>

.. vim: ts=3 sw=3 et tw=80
