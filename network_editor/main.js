/**
 * @fileoverview The main function for the Network Editor.
 */

var main = function() {
  var fdg = new ForceDirectedGraph(document.getElementById("fdg"));

  // Prepares reading from a file.
  var file_input = document.getElementById("file_input");
  file_input.addEventListener("change", function() {
    var file = file_input.files[0];
    var reader = new FileReader();
    reader.addEventListener("load", function() {
      fdg.Clear();
      fdg.Import(reader.result);
    });
    reader.readAsText(file);
  });

  // Registers handler for importing from a file.
  var import_elem = document.getElementById("import");
  import_elem.addEventListener("click", function() {
    file_input.click();
  });

  // Registers handler for exporting to a file.
  var export_elem = document.getElementById("export");
  export_elem.addEventListener("click", function() {
    var a = document.createElement("a");
    a.href = "data:application/json," + encodeURIComponent(fdg.Export());
    a.download = "data.json";
    a.click();
  });

  // Registers handler for clearing the force-directed graph.
  var clear_elem = document.getElementById("clear");
  clear_elem.addEventListener("click", function() {
    fdg.Clear();
  });
};
main();