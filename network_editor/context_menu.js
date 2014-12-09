/**
 * @fileoverview The context menu class, which can be used to create custom
 * context menus for any event target.
 */

/**
 * Constructs a context menu for a given element. The context menu
 * automatically replaces the default context menu for that element.
 * @param {EventTarget} elem The element to put the context menu on.
 * @constructor
 */
var ContextMenu = function (elem) {
  /**
   * The HTML element of the context menu.
   * @type {EventTarget}
   */
  this.elem = null;

  /**
   * The list of options in the context menu.
   * @type {Array.<Array.<string|function(number, number)>>}
   */
  this.opts = [];

  /**
   * The x position of the context menu.
   * @type {number}
   */
  this.x;

  /**
   * The y position of the context menu.
   * @type {number}
   */
  this.y;

  // Makes the context menu disappear when clicking somewhere else.
  window.addEventListener("click", function () {
    this.Remove();
  }.bind(this));

  // Creates the context menu.
  elem.addEventListener("contextmenu", function (e) {
    e.preventDefault();

    // Removes the context menu element if it exists.
    this.Remove();

    // Stores the x and y of where the context menu was created.
    this.x = e.x;
    this.y = e.y;

    // Creates the context menu element.
    this.elem = document.body.appendChild(document.createElement("div"));
    this.elem.className = "contextmenu";

    // Adds the options.
    for (var i = 0; i < this.opts.length; i++) {
      // Creates the HTML element and appends it to the document.
      var opt = document.createElement("div");
      opt.className = "opt";
      opt.textContent = this.opts[i][0];
      this.elem.appendChild(opt);

      // Adds the event listener for click.
      opt.addEventListener("click", function (i, e) {
        this.Remove();
        this.opts[i][1](this.x, this.y);
      }.bind(this, i));
    }

    // Positions the context menu.
    this.elem.style.left = e.x + (e.x < window.innerWidth -
        this.elem.offsetWidth ? 0 : - this.elem.offsetWidth) + "px";
    this.elem.style.top = e.y + (e.y < window.innerHeight -
        this.elem.offsetHeight ? 0 : - this.elem.offsetHeight) + "px";
  }.bind(this));
};

/**
 * Adds an option to the context menu.
 * @param {string} name The label of the context menu option.
 * @param {function(number, number)} onclick The function to call when the
 * option is selected. Passes on the x and y coordinates of the mouse when the
 * option was selected.
 */
ContextMenu.prototype.AddOpt = function (name, onclick) {
  this.opts.push([name, onclick]);
};

/**
 * Removes the HTML element of the context menu.
 */
ContextMenu.prototype.Remove = function () {
  if (this.elem === null) {
    return;
  }
  this.elem.parentNode.removeChild(this.elem);
  this.elem = null;
};