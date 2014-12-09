/**
 * @fileoverview Link class for links in the force-directed graph.
 */

/**
 * Constructs a link in the force-directed graph. The link is undirected, so
 * the first and second devices connected to this link are interchangeable.
 * @param {ForceDirectedGraph} fdg The force-directed graph to create the link
 * in.
 * @param {Device} device_a The first device.
 * @param {Device} device_b The second device.
 */
var Link = function(fdg, device_a, device_b) {
  /**
   * The force-directed graph that this link is in.
   * @type {ForceDirectedGraph}
   */
  this.fdg = fdg;

  /**
   * The first device.
   * @type {Device}
   */
  this.device_a = device_a;

  /**
   * The second device.
   * @type {Device}
   */
  this.device_b = device_b;

  /**
   * The HTML element representing this link.
   * @type {EventTarget}
   */
  this.elem = document.body.appendChild(document.createElement("div"));

  /**
   * The editable text.
   * @type {EditableText}
   */
  this.editable_text = new EditableText(this.elem);

  // Sets the element properties.
  this.elem.className = "link";

  // Adds the link to each device's list of links.
  this.device_a.AddLink(this);
  this.device_b.AddLink(this);

  // Sets up the context menu.
  var contextmenu = new ContextMenu(this.elem);
  contextmenu.AddOpt("Rename", this.FocusContent.bind(this));
  contextmenu.AddOpt("Delete", this.Remove.bind(this));

  // Renders the link.
  this.Render();
};

/**
 * Returns the label of the link.
 * @return {string} The label.
 */
Link.prototype.GetLabel = function() {
  return this.editable_text.GetText();
};

/**
 * Sets the label of the link.
 * @param {string} label The label to set the link to.
 */
Link.prototype.SetLabel = function(label) {
  this.editable_text.SetText(label);
};

/**
 * Focuses on the label of the link.
 */
Link.prototype.FocusContent = function() {
  this.editable_text.Clear();
  this.editable_text.Focus();
};

/**
 * Removes the link.
 */
Link.prototype.Remove = function() {
  // Removes the link from the two devices it links together.
  this.device_a.RemoveLink(this);
  this.device_b.RemoveLink(this);

  // Removes the link from the FDG.
  this.fdg.RemoveLink(this);
  this.elem.parentNode.removeChild(this.elem);
};

/**
 * Returns the other device connected to the link given a device that the link
 * is connected to.
 * @param {Device} device One of the devices that the link is connected to.
 */
Link.prototype.GetOtherDevice = function(device) {
  return device === this.device_a ? this.device_b : this.device_a;
};

/**
 * Renders the link.
 */
Link.prototype.Render = function() {
  // Line properties.
  this.fdg.ctx.lineWidth = 4;
  this.fdg.ctx.strokeStyle = "#d0d0d0";

  // Draws the line.
  this.fdg.ctx.beginPath();
  this.fdg.ctx.lineTo(this.device_a.x, this.device_a.y);
  this.fdg.ctx.lineTo(this.device_b.x, this.device_b.y);
  this.fdg.ctx.stroke();

  // Updates the element.
  this.elem.style.left = (this.device_a.x + this.device_b.x) / 2 + "px";
  this.elem.style.top = (this.device_a.y + this.device_b.y) / 2 + "px";
};