# smdv
a **s**imple **m**ark**d**own **v**iewer for linux.

## Dependencies

### Required
  - `python3` pointing to Python 3.6+.
  - [Pandoc](http://pandoc.org/) [`pip3 install pandoc` | `apt install pandoc` | `pacman -S pandoc` | ... ]
  - [Flask](http://flask.pocoo.org/) [`pip3 install flask` | `apt install python3-flask` | `pacman -S python-flask` | ... ]
  - [Websockets](https://websockets.readthedocs.io/) [`pip3 install websockets` | `apt install python3-websockets` | `pacman -S python-websockets` | ... ]

### Optional
  - [Jupyter](http://jupyter.org) (to view jupyter notebooks) [`pip3 install jupyter` | `apt install jupyter` | `pacman -S jupyter` | ... ]
  - [Neovim Remote](https://github.com/mhinz/neovim-remote) [`pip3 install neovim neovim-remote`]

## Installation
```
    pip3 install smdv
```

## Compatibility with neovim
This viewer was made with neovim compatibility in mind. With the use of `neovim-remote`,
this script is able to open files in the current neovim window (or spawn a new neovim
window if there is no window available).

However, to make it fully compatible with neovim and to make neovim able to sync
its current file to the viewer, [neovim-remote](https://github.com/mhinz/neovim-remote)
should be installed and the following lines should be added to your `init.vim`:

```
    " open / sync smdv
    autocmd FileType markdown nnoremap <F5> <Esc>:w<CR>:silent execute '!smdv 'expand('%:p')' -v "'.v:servername'"'<CR>

    " sync smdv on save
    autocmd BufWritePost *.md silent !smdv %
```
These settings enable (re)starting the smdv viewer when pressing `<F5>`, while
the markdown file will also be synced after every save.

## Compatibility with vim-instant-markdown
Alternatively, if syncing after every save is not enought, smdv can also be
used in conjuction with
[vim-instant-markdown](https://github.com/suan/vim-instant-markdown). Install the 
vim-plugin and add the following line to your vimrc:
```
let g:instant_markdown_python = 1
```
This line disables the default javascript daemon handling instant previews in favor of
smdv.


## Screenshots
### markdown preview
![smdv-dir](img/smdv-md.png)
### directory
![smdv-dir](img/smdv-dir.png)

