$(document).ready(function() {
    var mime = 'text/x-mariadb';
    cm = CodeMirror.fromTextArea(document.querySelector('#textbox'), {
        mode: mime,
        indentWithTabs: true,
        smartIndent: true,
        lineNumbers: true,
        matchBrackets : true,
        autofocus: true,
        extraKeys: {"Ctrl-Space": "autocomplete"},
        hintOptions: {tables: {
            aisles: ["aisle_id", "aisle"],
            departments: ["department_id", "department"],
            order_products: ["order_id", "product_id", "add_to_cart_order", "reordered"],
            order_products_prior: ["order_id", "product_id", "add_to_cart_order", "reordered"],
            orders: ["order_id", "user_id", "eval_set", "order_number", "order_dow", "order_hour_of_day", "days_since_prior_order"],
            products: ["product_id", "product_name", "aisle_id", "department_id"],
            ABC_Retail_Fact_Table: ["OrderID", "OrderDate", "Order_ShippedDate", "Order_Freight", "Order_ShipCity", "Order_ShipCountry", "Order_UnitPrice", "Order_Quantity", "Order_Amount", "ProductName"],
            ABC_Retail_Fact_Table_Revamp: ["OrderID", "OrderDate", "Order_ShippedDate", "Order_Freight", "Ship_City_ID", "Order_UnitPrice", "Order_Quantity", "Order_Amount", "Product_ID", "Employee_ID"],
            Country_City_dim: ["City_ID", "Country", "City"],
            Customer_dim: ["Customer_ID", "CompanyName", "ContactName", "Phone", "City_ID"],
            Employee_dim: ["Employee_ID", "LastName", "FirstName", "Title"],
            MyCube: ["ThisYear", "ThisQuarter", "Region", "Product", "Sales"],
            Product_dim: ["Product_ID", "ProductName"]
        }}
    });
    doc = cm.getDoc();
    window.editor = cm; 

    $('#history-tab').click(function() {
        get_saved_data();
    });

    $('#submit-button').click(function() {
        cm.save();
        $('#submit-button').css('display', 'none');
        $('#loading').css('display', 'inline-block');
        query = getSelectedTextById("textbox");
        database_type = $('input[name=database_type]:checked').val()
        get_output(query, database_type);
    })
    $('#history-tab').click();
});3

function get_output(query, database_type) {
    let obj_len = null;
    let rowCount = null;
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
                obj_len = rows.length;
                rowCount = data['row_count'];
                if (rowCount == '0' || rows.length == 0) {
                    refreshTable('display-table', 'display-table');
                    refreshTable('summary-table', 'summary-table');
                    $('#history-tab').click();
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
                $('#history-tab').click();
            }
            displayMessage(
              data['success'], data['row_count'], data['run_time'], rowCount, obj_len, data["is_truncated"], data['summary']
            );
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

function displayMessage(code, num_rows, run_time, row_count, obj_len, is_truncated, exception_message) {
  console.log(exception_message);
  if (code) {
    $("#success-message").css("display", "block");
    $("#error-message").css("display", "none");
    $("#success-rowcount").text("Number of rows: " + num_rows.toString());
    $("#success-time").text("Runtime: " + run_time.toString());
    if (is_truncated) {
      $('#success-is-truncated').css("display", "block");
      $('#success-is-truncated').html("<b>Truncated from " + row_count.toString() + " to " + obj_len.toString() + '</b>');
    } else {
      $('#success-is-truncated').css("display", "none");
    }
  } else {
      $("#success-message").css("display", "none");
      $("#error-message").css("display", "block");
      $("#error-message").text(exception_message)
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
    if (doc.somethingSelected())
        return doc.getSelection();
    return (query = $("#" + id).val());
}

function add_history_click(){
      $('#history-table tbody').on('click', 'tr', function () {
        var table = $('#history-table').DataTable();
        var data = table.row( this ).data();
        if(data["query_text"].length >0)
          $("#textbox").val(data["query_text"])
          doc.setValue(data["query_text"]);
        // $('#textbox').focus();
        // cm.getInputField()
        cm.focus()
      } );
}