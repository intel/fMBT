;; Copyright 2014, Intel Corporation

;; Author: Antti Kervinen <antti.kervinen@intel.com>
;; Created: Jan 2013
;; $Revision: 0.0 $

;; This file is free software; you can redistribute it and/or modify
;; it under the terms of the GNU General Public License as published by
;; the Free Software Foundation, either version 3 of the License, or
;; (at your option) any later version.

;; This file is distributed in the hope that it will be useful,
;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;; GNU General Public License for more details.

;; You should have received a copy of the GNU General Public License
;; along with GNU Emacs.  If not, see <http://www.gnu.org/licenses/>.

;;; Commentary:

;; This provides a mode for editing AAL/Python.
;;
;; I have used http://www.emacswiki.org/emacs/ModeTutorial
;; as an example.


(defvar aal-mode-hook nil)

(defvar aal-indent 4)

(defvar aal-indent-latest nil)

(defvar aal-mode-map
  (let ((map (make-keymap)))
    (define-key map "\C-j" 'newline-and-indent)
    map)
  "Keymap for (pure) AAL mode")

; optimised regexps for highlighting
(defconst aal-font-lock-keywords
  (list
   (cons
    "^\s*#.*$"
    font-lock-comment-face)
   (cons
    (regexp-opt '("aal" "language" "variables"
                  "action" "input" "output"
                  "tag" "parallel" "serial"))
    font-lock-keyword-face)
    (cons
     (regexp-opt '("guard" "guard()"
                   "adapter" "adapter()"
                   "body" "body()"
                   "initial_state" "adapter_init" "adapter_exit"))
     font-lock-function-name-face)
   (cons
    "\\(?:\\^\\(?:endif\\|i\\(?:fdef\\|nclude\\)\\)\\)"
    font-lock-preprocessor-face)
   )
  "Syntax highlighting for pure AAL code")

(defun char-count (char str)
  (if (= 0 (length str))
      0
    (if (= char (aref str 0))
        (+ 1 (char-count char (substring str 1)))
      (char-count char (substring str 1)))))

(defun chars-count (chars str)
  (if (= 0 (length chars))
      0
    (+ (chars-count (substring chars 1) str)
       (char-count (aref chars 0) str))))

(defun line-opens-block ()
  (or
   (looking-at "^.*[[({:][ \t]*$")
   (> (chars-count "({[" (thing-at-point 'line))
      (chars-count ")}]" (thing-at-point 'line)))
   ))

(defun line-closes-block ()
  (< (chars-count "({[" (thing-at-point 'line))
     (chars-count ")}]" (thing-at-point 'line)))
  )

(defun aal-do-indent-line()
  (let (prev-line-opens-block
        prev-line-closes-block
        prev-indent)
    (save-excursion
      ; goto previous non-empty line
      (while (progn (forward-line -1)
                    (and (not (bobp))
                         (eq (point-at-bol) (point-at-eol)))))
      (setq prev-line-opens-block (line-opens-block))
      (setq prev-line-closes-block (line-closes-block))
      (setq prev-indent (current-indentation)))
    (if (line-closes-block)
        (indent-line-to (max 0 (- prev-indent aal-indent)))
        (if prev-line-opens-block ; Previous line opens a block
            (indent-line-to (+ prev-indent aal-indent))
          (indent-line-to prev-indent) ; Default
          ))))

(defun aal-do-indent-next-depth ()
  (let ((new-indent (- (current-indentation) aal-indent)))
    (if (< new-indent 0)
        (aal-do-indent-line)
      (indent-line-to new-indent))))

(defun aal-indent-line ()
  "Indent current line in AAL"
  (interactive)
  (let ((indent-again (eq (count-lines 1 (point)) aal-indent-latest)))
    (beginning-of-line)
    (if indent-again
        (aal-do-indent-next-depth)
      (aal-do-indent-line))
    (end-of-line)
    )
  (setq aal-indent-latest (count-lines 1 (point))))

(defun aal-mode ()
  "Major mode for pure AAL"
  (interactive)
  (kill-all-local-variables)
  (use-local-map aal-mode-map)
  (set (make-local-variable 'font-lock-defaults) '(aal-font-lock-keywords))
  (set (make-local-variable 'indent-line-function) 'aal-indent-line)
  (setq major-mode 'aal-mode)
  (setq mode-name "AAL")
  (run-hooks 'aal-mode-hook))

(provide 'aal-mode)

(add-to-list 'auto-mode-alist '("\\.aal\\'" . aal-mode))
