$(document).ready(function() {
    $('#history-tab').click(function() {
        get_saved_data();
        
    });

    $('#submit-button').click(function() {
        $('#submit-button').css('display', 'none');
        $('#loading').css('display', 'block');
        query = getSelectedTextById("textbox");
        database_type = $('input[name=database_type]:checked').val()
        get_output(query, database_type);
    })
    $('#history-table tbody>tr').click(function () {
      var table = $('#history-table').DataTable();
      var data = table.row( this ).data();
      alert( 'You clicked on '+data[0]+'\'s row' );
    } );
    $('#history-tab').click();
});

function get_output(query, database_type) {
    $.ajax({
        type: "POST",
        dataType: "json",
        url: "/post",
        data: {
            query_string: query, 
            database_type: database_type
        },
        success: function(data) {
            $('#submit-button').css('display', 'block');
            $('#loading').css('display', 'none');
            if (data['success']) {
                rows = JSON.parse(data['rows']);
                rowCount = data['row_count'];
                if (rowCount == '0' || rows.length == 0) {
                    refreshTable('display-table', 'display-table');
                    refreshTable('summary-table', 'summary-table');
                } else {
                    $('#output-tab').click();
                    $('#output-tab').css('display', 'block');
                    $('#summary-tab').css('display', 'block');
                    loadTable(rows, data['delimiter'], 'display-table', 'display-table');
                    loadTable(JSON.parse(data['summary']), data['delimiter'], 'summary-table', 'summary-table');
                }
            } else {
                refreshTable('display-table', 'display-table');
                refreshTable('summary-table', 'summary-table');
            }
            displayMessage(data['success'], data['row_count'], data['run_time']);
        }
    });
}

function loadTable(data, delim, id, class_) {
    column_object = [];
    for (key in data[0]) {
        column_object.push({
            title: key.replaceAll(delim, ''),
            data: key
        })
    }

    refreshTable(class_, id);
    $('#' + id).DataTable({
      dom: 'Bfrtip',
        buttons: [
            'copyHtml5',
            'excelHtml5',
            'csvHtml5',
            'pdfHtml5'
        ],
        bSort: false,
        data : data,
        // "bPaginate": false,
        bFilter: true,
        bInfo: true,
        columns: column_object,
        
    });
    add_history_click();
};

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

function get_saved_data() {
    $.ajax({
      type: "POST",
      url: "/get_query_history",    
      success: function (data) {
        loadTable(JSON.parse(data), '$|$|', 'history-table', 'history-table');
      },
    });
  }


function refreshTable(class_, id) {
    $('.' + class_).remove('#' + id);
    $('.' + class_).html("<table id='" + id + "'></table>")
}

function getSelectedTextById(id) {
  var txtArea = document.getElementById(id);
  var startPost = txtArea.selectionStart;
  var endPos = txtArea.selectionEnd;
  var selectedText = txtArea.value.substring(startPost, endPos);

  if (selectedText.length <= 0) {
    return (query = $("#textbox").val());
  } else {
    return selectedText;
  }
}
function add_history_click(){
  $('#history-table tbody>tr').click(function () {
    var table = $('#history-table').DataTable();
    var data = table.row( this ).data();
    if(data["query_text"].length >0)
      $("#textbox").val(data["query_text"])
  } );
}
