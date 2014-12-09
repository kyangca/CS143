/**
 * @fileoverview The force-directed graph for the network editor.
 */

/**
 * Computes the norm of a two-dimensional vector.
 * @param {number} dx The first number.
 * @param {number} dy The second number.
 */
var ComputeNorm = function(dx, dy) {
  return Math.sqrt(dx * dx + dy * dy);
};

/**
 * Constructs a force-directed graph.
 * @param {EventTarget} canvas The HTML element of the canvas to use.
 * @constructor
 */
var ForceDirectedGraph = function(canvas) {
  /**
   * The canvas element.
   * @type {EventTarget}
   */
  this.canvas = canvas;

  /**
   * The context for the canvas element.
   * @type {CanvasRenderingContext2D}
   */
  this.ctx = canvas.getContext("2d");

  /**
   * The list of devices in the force-directed graph.
   * @type {Array.<Device>}
   */
  this.devices = [];

  /**
   * The list of links in the force-directed graph.
   * @type {Array.<Link>}
   */
  this.links = [];

  /**
   * -1 if not selecting a device. Otherwise n for selecting the nth device.
   * @type {number}
   */
  this.selecting_device = -1;

  /**
   * The list of selected devices. Used when creating a link.
   * @type {Array.<Device>}
   */
  this.selected_devices = [];

  /**
   * The hint element when there no devices in the force-directed graph. Tells
   * the user how to get started rather than just presenting an empty screen.
   * @type {EventTarget}
   */
  this.hint_elem = document.body.appendChild(document.createElement("div"));

  /**
   * The repulsive constant used in the force equation akin to Coulomb's law
   * used in the force-directed graph simulation.
   * @type {number}
   */
  this.device_repulsive_k = 100000;

  /**
   * The spring constant used in the spring equation akin to the damped
   * Hooke's law used in the force-directed graph simulation.
   * @type {number}
   */
  this.device_spring_k = .02;

  /**
   * The preferred spring length used in the spring equation akin to the
   * damped Hooke's law used in the force-directed graph simulation.
   * @type {number}
   */
  this.device_spring_x = 0;

  /**
   * The spring damping constant used in the spring equation akin to the
   * damped Hooke's law used in the force-directed graph simulation.
   * @type {number}
   */
  this.device_spring_c = .2;

  /**
   * The x of the collective velocity of all devices with links, used for
   * springing the collective network to the center of the screen.
   * @type {number}
   */
  this.vx = 0;

  /**
   * The y of the collective velocity of all devices with links, used for
   * springing the collective network to the center of the screen.
   * @type {number}
   */
  this.vy = 0;

  // Adds hint element to get started.
  this.hint_elem.className = "hint";
  this.hint_elem.textContent = "Right-click anywhere to get started.";

  // Creates the context menu object.
  var contextmenu = new ContextMenu(this.canvas);
  contextmenu.AddOpt("Create Host", this.AddHost.bind(this));
  contextmenu.AddOpt("Create Link", this.StartSelectingBothDevicesToLink.bind(
      this));
  contextmenu.AddOpt("Create Router", this.AddRouter.bind(this));

  // Resizes to background size.
  this.ResizeFull();
  window.addEventListener("resize", this.ResizeFull.bind(this));

  // Adds handler to stop selecting device to link.
  window.addEventListener("keydown", function(e) {
    if (e.keyCode === 27) {
      this.StopSelectingDeviceToLink();
    }
  }.bind(this));

  // Starts the force-directed graph.
  window.requestAnimationFrame(this.Run.bind(this));
};

/**
 * Resizes the canvas to the full size of the window.
 */
ForceDirectedGraph.prototype.ResizeFull = function() {
  this.canvas.width = window.innerWidth;
  this.canvas.height = window.innerHeight;
};

/**
 * Adds a new host at the given position.
 * @param {number} x The position's x coordinate.
 * @param {number} y The position's y coordinate.
 * @return {Host} The new host.
 */
ForceDirectedGraph.prototype.AddHost = function(x, y) {
  var host = new Host(this, x, y);
  this.devices.push(host);
  return host;
};

/**
 * Adds a new router at the given position.
 * @param {number} x The position's x coordinate.
 * @param {number} y The position's y coordinate.
 * @return {Router} The new router.
 */
ForceDirectedGraph.prototype.AddRouter = function(x, y) {
  var router = new Router(this, x, y);
  this.devices.push(router);
  return router;
};

/**
 * Creates a new link linking together two devices.
 * @param {Device} device_a The first device.
 * @param {Device} device_b The second device.
 * @return {Link} The new link.
 */
ForceDirectedGraph.prototype.AddLink = function(device_a, device_b) {
  var link = new Link(this, device_a, device_b);
  this.links.push(link);
  return link;
};

/**
 * Starts the process of the user selecting two devices to link together to
 * create a link.
 * @param {number} x The x coordinate passed on by the context-menu object.
 * @param {number} y The y coordinate passed on by the context-menu object.
 */
ForceDirectedGraph.prototype.StartSelectingBothDevicesToLink = function(x, y) {
  // We are now selecting device 0.
  this.selecting_device = 0;

  // Highlights devices.
  this.HighlightDevices();
};

/**
 * Starts the process of the user selecting a device to create a link from a
 * given device.
 * @param {Device} device The device linking from.
 */
ForceDirectedGraph.prototype.StartSelectingSecondDeviceToLink = function(device
    ) {
  this.StartSelectingBothDevicesToLink();
  this.SelectDevice(device);
};

/**
 * Stops the process of the user selecting a device to link together.
 */
ForceDirectedGraph.prototype.StopSelectingDeviceToLink = function() {
  // Resets the selecting devices flag and selected devices.
  this.selecting_device = -1;
  this.selected_devices = [];

  // Unhighlights devices.
  this.UnhighlightDevices();
};

/**
 * Highlights all devices for use in selecting devices to link together.
 */
ForceDirectedGraph.prototype.HighlightDevices = function() {
  for (var i = 0; i < this.devices.length; i++) {
    this.devices[i].Highlight();
  }
};

/**
 * Unhighlights all devices for use in selecting devices to link together.
 */
ForceDirectedGraph.prototype.UnhighlightDevices = function() {
  for (var i = 0; i < this.devices.length; i++) {
    this.devices[i].Unhighlight();
  }
};

/**
 * Removes a device from the list of devices.
 * @param {Device} device The device to remove.
 */
ForceDirectedGraph.prototype.RemoveDevice = function(device) {
  // Finds the device. O(n) operation.
  var i = this.devices.indexOf(device);

  // Removes the device.
  this.devices[i] = this.devices[this.devices.length - 1];
  this.devices.pop();
};

/**
 * Removes a link from the list of links.
 * @param {Link} link The link to remove.
 */
ForceDirectedGraph.prototype.RemoveLink = function(link) {
  // Finds the device. O(n) operation.
  var i = this.links.indexOf(link);

  // Removes the device.
  this.links[i] = this.links[this.links.length - 1];
  this.links.pop();
};

/**
 * Selects a device when creating a link.
 * @param {Device} device The device to select.
 */
ForceDirectedGraph.prototype.SelectDevice = function(device) {
  // The nth device is being selected if n > -1.
  if (this.selecting_device > -1) {
    // Checks that the device is a different device.
    if (this.selected_devices.indexOf(device) !== -1) {
      return;
    }

    // Selects the device.
    this.selected_devices[this.selecting_device] = device;
    this.selecting_device++;
    device.HighlightAsSelected();

    // Once two devices are selected, the link is created.
    if (this.selecting_device == 2) {
      // Creates the link.
      var link = new Link(this, this.selected_devices[0],
          this.selected_devices[1]);
      this.links.push(link);

      this.StopSelectingDeviceToLink();
    }
  }
};

/**
 * Clears the rendering area and renders all devices and links.
 */
ForceDirectedGraph.prototype.Render = function() {
  this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

  if (this.devices.length === 0) {
    this.hint_elem.classList.remove("display_none");
  } else {
    this.hint_elem.classList.add("display_none");
  }

  for (var i = 0; i < this.devices.length; i++) {
    this.devices[i].Render();
  }

  for (var i = 0; i < this.links.length; i++) {
    this.links[i].Render();
  }
};

/**
 * Runs a discrete-time step of the simulation of the force-directed graph.
 */
ForceDirectedGraph.prototype.Run = function() {
  // Repulsive forces with all other devices with links.
  for (var i = 0; i < this.devices.length; i++) {
    var a = this.devices[i];
    if (a.links.length === 0) {
      continue;
    }

    for (var j = i + 1; j < this.devices.length; j++) {
      var b = this.devices[j];
      if (b.links.length === 0) {
        continue;
      }

      var dx = b.x - a.x;
      var dy = b.y - a.y;
      var r = ComputeNorm(dx, dy);
      dx /= r;
      dy /= r;
      var f = -this.device_repulsive_k / (r * r);
      var ax = f * dx;
      var ay = f * dy;
      a.vx += ax;
      a.vy += ay;
      b.vx -= ax;
      b.vy -= ay;
    }
  }

  // Spring forces between linked devices.
  for (var i = 0; i < this.links.length; i++) {
    var a = this.links[i].device_a;
    var b = this.links[i].device_b;

    var dx = b.x - a.x;
    var dy = b.y - a.y;
    var r = ComputeNorm(dx, dy);
    dx /= r;
    dy /= r;
    var f = this.device_spring_k * (r - this.device_spring_x);
    var ax = f * dx + this.device_spring_c * (b.vx - a.vx);
    var ay = f * dy + this.device_spring_c * (b.vy - a.vy);
    a.vx += ax;
    a.vy += ay;
    b.vx -= ax;
    b.vy -= ay;
  }

  // Computes the center of mass for devices with links.
  var x = 0;
  var y = 0;
  var count = 0;
  for (var i = 0; i < this.devices.length; i++) {
    var device = this.devices[i];
    if (device.links.length > 0) {
      x += device.x;
      y += device.y;
      count++;
    }
  }
  if (count > 0) {
    x /= count;
    y /= count;

    // Computes the spring force with the center of the window.
    var cx = window.innerWidth / 2;
    var cy = window.innerHeight / 2;
    var dx = cx - x;
    var dy = cy - y;
    var ax = this.device_spring_k * dx - this.device_spring_c * this.vx;
    var ay = this.device_spring_k * dy - this.device_spring_c * this.vy;
    this.vx += ax;
    this.vy += ay;
  }

  // Updates positions based on velocities.
  for (var i = 0; i < this.devices.length; i++) {
    var device = this.devices[i];
    if (device.links.length > 0) {
      device.x += device.vx;
      device.y += device.vy;
      device.x += this.vx;
      device.y += this.vy;
    }
  }

  this.Render();

  window.requestAnimationFrame(this.Run.bind(this));
};

/**
 * Imports a file into the force-directed graph.
 * @param {string} json The string containing the JSON of the network.
 */
ForceDirectedGraph.prototype.Import = function(json) {
  var json = JSON.parse(json);
  var x_spacing = 128;
  var y_spacing = 128;
  var x = x_spacing;
  var y = window.innerHeight / 2;

  var devices = {};

  // Loads hosts from the JSON data.
  for (var i = 0; i < json["hosts"].length; i++) {
    var json_host = json["hosts"][i];
    var label = json_host["id"];

    devices[label] = this.AddHost(x, y);
    devices[label].SetLabel(label);
    x += x_spacing;
    y += y_spacing * Math.random() - y_spacing / 2;
  }

  // Loads routers from the JSON data.
  for (var i = 0; i < json["routers"].length; i++) {
    var json_router = json["routers"][i];
    var label = json_router["id"];

    devices[label] = this.AddRouter(x, y);
    devices[label].SetLabel(label);
    x += x_spacing;
    y += y_spacing * Math.random() - y_spacing / 2;
  }

  // Loads links from the JSON data.
  for (var i = 0; i < json["links"].length; i++) {
    var json_link = json["links"][i];
    var label = json_link["id"];

    var device_a = devices[json_link["left_device_id"]];
    var device_b = devices[json_link["right_device_id"]];
    var link = this.AddLink(device_a, device_b);
    link.SetLabel(label);
  }
};

/**
 * Exports the graph into JSON.
 * @return {string} The string containing the JSON of the exported graph.
 */
ForceDirectedGraph.prototype.Export = function() {
  var json = {
    "flows": [],
    "hosts": [],
    "links": [],
    "routers": [],
  };

  for (var i = 0; i < this.devices.length; i++) {
    var device = this.devices[i];
    var key = device instanceof Host ? "hosts" : "routers";
    json[key].push({
      "id": device.GetLabel(),
      "links": device.GetLinkLabels(),
    });
  }

  return JSON.stringify(json, null, 2);
};

/**
 * Clears the graph by removing all devices and links.
 */
ForceDirectedGraph.prototype.Clear = function() {
  // Removes all devices. This will also remove all links.
  while (this.devices.length > 0) {
    this.devices[0].Remove();
  }

  this.Render();
};