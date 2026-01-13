(function () {
  // --- 1) Define a minimal SML mode for CodeMirror 5 ---
  CodeMirror.defineMode("sml", function () {
    const keywords = new Set([
      "fun","val","type","datatype","exception","structure","signature","functor",
      "let","in","end","if","then","else","case","of","fn","raise","handle",
      "local","open","rec","and","with","withtype","abstype","as","op","while","do"
    ]);

    function tokenBase(stream, state) {
      // Nested comments: (* ... (* ... *) ... *)
      if (state.inComment > 0) {
        if (stream.match("(*")) { state.inComment++; return "comment"; }
        if (stream.match("*)")) { state.inComment--; return "comment"; }
        stream.next();
        return "comment";
      }

      if (stream.match("(*")) { state.inComment = 1; return "comment"; }

      // Strings
      if (stream.peek() === '"') {
        stream.next();
        while (!stream.eol()) {
          const ch = stream.next();
          if (ch === "\\") stream.next();      // escape char
          else if (ch === '"') break;          // end string
        }
        return "string";
      }

      // Whitespace
      if (stream.eatWhile(/\s/)) return null;

      // Numbers
      if (stream.match(/^\d+(\.\d+)?/)) return "number";

      // Identifiers / keywords (allow ' in identifiers)
      if (stream.match(/^[A-Za-z_][A-Za-z0-9_']*/)) {
        const w = stream.current();
        if (keywords.has(w)) return "keyword";
        if (/^[A-Z]/.test(w)) return "variable-2"; // constructors/types-ish
        return "variable";
      }

      // Operators
      if (stream.match(/^[:=!<>+\-*/@^|&#$%~?]+/)) return "operator";

      stream.next();
      return null;
    }

    return {
      startState: () => ({ inComment: 0 }),
      token: tokenBase
    };
  });

  // --- 2) Mount CodeMirror onto a textarea with a specific ID ---
  function mountSmlEditor(textareaId) {
    const textarea = document.getElementById(textareaId);
    if (!textarea) return null;

    window.codeMirrorEditor = CodeMirror.fromTextArea(textarea, {
        mode: "sml",
        lineNumbers: true,
        indentUnit: 2,
        tabSize: 2,
        lineWrapping: true,
        theme: "pals",
    });

    return window.codeMirrorEditor;
  }

  // --- 3) Auto-mount when DOM is ready ---
  document.addEventListener("DOMContentLoaded", function () {
    mountSmlEditor("code-input-area");
  });

  // Optional: expose function in case you want manual mounting later
  window.mountSmlEditor = mountSmlEditor;
})();