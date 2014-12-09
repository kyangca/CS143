/**
 * @fileoverview Device class and derived classes Host and Router.
 */

/**
 * The base class for devices in the force-directed graph.
 * @param {ForceDirectedGraph} fdg The force-directed graph that this device
 * is in.
 * @param {number} x The x position to create the device at.
 * @param {number} y The y position to create the device at.
 * @constructor
 */
var Device = function(fdg, x, y) {
  /**
   * The force-directed graph that this device is in.
   * @type {ForceDirectedGraph}
   */
  this.fdg = fdg;

  /**
   * The HTML element representing this device.
   * @type {EventTarget}
   */
  this.elem = document.body.appendChild(document.createElement("div"));

  /**
   * The editable text.
   * @type {EditableText}
   */
  this.editable_text = new EditableText(this.elem);

  /**
   * The x position of the device in the force-directed graph.
   * @type {number}
   */
  this.x = x;

  /**
   * The y position of the device in the force-directed graph.
   * @type {number}
   */
  this.y = y;

  /**
   * The x velocity of the device in the force-directed graph.
   * @type {number}
   */
  this.vx = 0;

  /**
   * The y velocity of the device in the force-directed graph.
   * @type {number}
   */
  this.vy = 0;

  /**
   * The links connected to this device.
   * @type {Array.<Link>}
   */
  this.links = [];

  // Positions the device.
  this.Render();

  // Adds the context menu for the device.
  var contextmenu = new ContextMenu(this.elem);
  contextmenu.AddOpt("Link To...", this.StartSelectingSecondDeviceToLink.bind(
      this));
  contextmenu.AddOpt("Rename", this.FocusContent.bind(this));
  contextmenu.AddOpt("Delete", this.Remove.bind(this));

  // Focuses on content on click.
  this.elem.addEventListener("click", function() {
    this.fdg.SelectDevice(this);
  }.bind(this));
};

/**
 * Returns the label of the device.
 * @return {string} The label.
 */
Device.prototype.GetLabel = function() {
  return this.editable_text.GetText();
};

/**
 * Sets the label of the device.
 * @param {string} label The label to set the device to.
 */
Device.prototype.SetLabel = function(label) {
  this.editable_text.SetText(label);
};

/**
 * Returns the list of labels of links connected to this device.
 * @return {Array.<string>} The list of labels of links.
 */
Device.prototype.GetLinkLabels = function() {
  return this.links.map(function(link) {
    return link.GetLabel();
  });
};

/**
 * Starts selecting the second device to link, using this device as the first.
 * @param {number} x The x position passed on by the context menu.
 * @param {number} y The y position passed on by the context menu.
 */
Device.prototype.StartSelectingSecondDeviceToLink = function(x, y) {
  this.fdg.StartSelectingSecondDeviceToLink(this);
};

/**
 * Adds a link to this device.
 * @param {Link} link The link to add.
 */
Device.prototype.AddLink = function(link) {
  this.links.push(link);
};

/**
 * Removes a link from this device.
 * @param {Link} link The link to remove.
 */
Device.prototype.RemoveLink = function(link) {
  // Finds the device. O(n) operation.
  var i = this.links.indexOf(link);

  // Removes the device.
  this.links[i] = this.links[this.links.length - 1];
  this.links.pop();

  // If no links, then stop moving.
  if (this.links.length === 0) {
    this.vx = 0;
    this.vy = 0;
  }
};

/**
 * Renders the device.
 */
Device.prototype.Render = function() {
  this.elem.style.left = this.x + "px";
  this.elem.style.top = this.y + "px";
};

/**
 * Focuses on the label of the device.
 */
Device.prototype.FocusContent = function() {
  this.editable_text.Clear();
  this.editable_text.Focus();
};

/**
 * Removes the HTML element of this device.
 */
Device.prototype.Remove = function() {
  // Removes all links connected to this device.
  while (this.links.length > 0) {
    this.links[0].Remove();
  }

  // Removes the device from the force directed graph.
  this.fdg.RemoveDevice(this);
  this.elem.parentNode.removeChild(this.elem);
};

/**
 * Highlights this device.
 */
Device.prototype.Highlight = function() {
  this.elem.classList.add("selecting_device");
};

/**
 * Unhighlights this device.
 */
Device.prototype.Unhighlight = function() {
  this.elem.classList.remove("selecting_device");
  this.elem.classList.remove("selected_device");
};

/**
 * Highlights this device as a selected device.
 */
Device.prototype.HighlightAsSelected = function() {
  this.elem.classList.remove("selecting_device");
  this.elem.classList.add("selected_device");
};


/**
 * Represents a host in the force-directed graph.
 * @param {ForceDirectedGraph} fdg The force-directed graph that this host is
 * in.
 * @param {number} x The x position to create the device at.
 * @param {number} y The y position to create the device at.
 * @constructor
 * @extends {Device}
 */
var Host = function(fdg, x, y) {
  Device.call(this, fdg, x, y);
  this.elem.className = "host";
};
Host.prototype = Object.create(Device.prototype);


/**
 * Represents a router in the force-directed graph.
 * @param {ForceDirectedGraph} fdg The force-directed graph that this router
 * is in.
 * @param {number} x The x position to create the device at.
 * @param {number} y The y position to create the device at.
 * @constructor
 * @extends {Device}
 */
var Router = function(fdg, x, y) {
  Device.call(this, fdg, x, y);
  this.elem.className = "router";
};
Router.prototype = Object.create(Device.prototype);