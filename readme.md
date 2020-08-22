# smdv

a **s**imple **m**ark**d**own **v**iewer for linux.

## Dependencies

### Required

- `python3` pointing to Python 3.6+.
- [Pandoc](http://pandoc.org/) 2.0+ [`apt install pandoc` | `pacman -S pandoc` | ... ]
- [Flask](http://flask.pocoo.org/) [`pip3 install flask` | `apt install python3-flask` | `pacman -S python-flask` | ... ]
- [Websockets](https://websockets.readthedocs.io/) [`pip3 install websockets` | `apt install python3-websockets` | `pacman -S python-websockets` | ... ]

### Optional

- [Jupyter](http://jupyter.org) (to view jupyter notebooks) [`pip3 install jupyter` | `apt install jupyter` | `pacman -S jupyter` | ... ]
- [Neovim Remote](https://github.com/mhinz/neovim-remote) [`pip3 install neovim neovim-remote`]

## Installation

```
    pip3 install smdv
```

## Configuration

smdv listens to a single environment variable: `SMDV_DEFAULT_ARGS`. As an example, below
you can see how smdv can be configured to always open in firefox on port 9999 by placing
the following line in your `.bashrc`:

```
SMDV_DEFAULT_ARGS="--browser firefox --port 9999"
```

Consult `smdv --help` to see which flags can be used.

## Compatibility with neovim

This viewer was made with neovim compatibility in mind. With the use of `neovim-remote`,
this script is able to open files in the current neovim window (or spawn a new neovim
window if there is no window available).

However, to make it fully compatible with neovim and to make neovim able to sync
its current file to the viewer, [neovim-remote](https://github.com/mhinz/neovim-remote)
should be installed and the following line should be added to your `init.vim`:

```
    " sync on save
    autocmd BufWritePost *.md silent execute '!smdv 'expand('%:p')' -v "'.v:servername'"'
```

This setting will sync the file to the viewer after every save.

## Compatibility with vim-instant-markdown

Alternatively, if syncing after every save is not enough, smdv can also be used
in conjuction with
[vim-instant-markdown](https://github.com/suan/vim-instant-markdown) for
instant markdown previews. Install the vim-plugin and add the following line to
your vimrc:

```
let g:instant_markdown_python = 1
```

This line disables the default javascript daemon handling instant previews in favor of
smdv. Consider removing the _sync-on-save_ line defined above when using this
option; both options are not completely compatible.

## Screenshots

### markdown preview

![smdv-dir](img/smdv-md.png)

### folder view

![smdv-dir](img/smdv-dir.png)
