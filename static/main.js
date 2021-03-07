$(document).ready(function () {
  $("#submit-button").click(function () {
    $("#submit-button").css("display", "none");
    $("#loading").css("display", "block");
    query = $("#textbox").val();
    database_type = $("input[name=database_type]:checked").val();
    $.ajax({
      type: "POST",
      dataType: "json",
      url: "/post",
      data: {
        query_string: query,
        database_type: database_type,
      },
      success: function (data) {
        $("#submit-button").css("display", "block");
        $("#loading").css("display", "none");
        if (data["success"]) {
          rows = JSON.parse(data["rows"]);
          rowCount = data["row_count"];
          if (rowCount == "0" || rows.length == 0) {
            refreshTable();
          } else {
            loadTable(rows, data["delimiter"]);
          }
        } else {
          refreshTable();
        }
        displayMessage(data["success"], data["row_count"], data["run_time"]);
      },
    });
  });
});

function loadTable(data, delim) {
  column_object = [];
  for (key in data[0]) {
    column_object.push({
      title: key.replaceAll(delim, ""),
      data: key,
    });
  }

  refreshTable();
  $("#display-table").DataTable({
    bSort: false,
    data: data,
    // "bPaginate": false,
    bFilter: true,
    bSort: true,
    bInfo: true,
    columns: column_object,
  });
}

function displayMessage(code, num_rows, run_time) {
  if (code) {
    $("#success-message").css("display", "block");
    $("#error-message").css("display", "none");
    $("#success-rowcount").text("Rows affected: " + num_rows.toString());
    $("#success-time").text("Runtime: " + run_time.toString());
  } else {
    $("#success-message").css("display", "none");
    $("#error-message").css("display", "block");
  }
}

function refreshTable() {
  $(".display-table").remove("#display-table");
  $(".display-table").html("<table id='display-table'></table>");
}

function get_saved_data(){
  $.ajax({
    type: "POST",
    url: "/get_query_history",    
    success: function (data) {
      console.log(data)
    },
  });
}