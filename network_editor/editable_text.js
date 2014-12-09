/**
 * @fileoverview The editable text class for adding editability to HTML
 * elements.
 */

/**
 * Constructs editable text. The object creates a div where the text can be
 * edited.
 * @param {EventTarget} parent_elem The parent element of the editable text.
 * @constructor
 */
var EditableText = function(parent_elem) {
  /**
   * The parent element of the editable text.
   * @type {EventTarget}
   */
  this.parent_elem = parent_elem;

  /**
   * The HTML element of the editable text.
   * @type {EventTarget}
   */
  this.elem = this.parent_elem.appendChild(document.createElement("div"));

  // Creates the text label element.
  this.elem.className = "content";
  this.elem.style.display = "inline";
  this.elem.contentEditable = true;
  this.elem.spellcheck = false;
  this.Focus();

  // Prevents effects of pressing enter.
  this.elem.addEventListener("keydown", function(e) {
    if (e.keyCode === 13) {
      e.preventDefault();
    }
  });

  // When the parent is clicked, focus on the content.
  this.parent_elem.addEventListener("click", function() {
    this.elem.focus();
  }.bind(this));
};

/**
 * Clears the editable text.
 */
EditableText.prototype.Clear = function() {
  this.elem.textContent = "";
};

/**
 * Sets the text in the editable text.
 * @param {string} text The text to set to.
 */
EditableText.prototype.SetText = function(text) {
  this.elem.textContent = text;
};

/**
 * Returns the text in the editable text.
 * @return {string} The text.
 */
EditableText.prototype.GetText = function() {
  return this.elem.textContent;
};

/**
 * Focuses on the editable text.
 */
EditableText.prototype.Focus = function() {
  this.elem.focus();
};