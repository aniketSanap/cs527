$(document).ready(function() {
    $('#submit-button').click(function() {

        query = $("#textbox").val()
        database_type = $('input[name=database_type]:checked').val()
        $.ajax({
            type: "POST",
            dataType: "json",
            url: "/post",
            data: {
                query_string: query, 
                database_type: database_type
            },
            success: function(data) {
                // console.log(data);
                loadTable(data);
            }
        });








        // $('#display-table').DataTable({
        //     // data : jsdata.list.event,
        //     // columns : [ {
        //     //     title : "Id",
        //     //     data : 'id'
        //     // }, {
        //     //     title : "Level",
        //     //     data : 'level'
        //     // }, {
        //     //     title : "Name",
        //     //     data : 'name'
        //     // }, {
        //     //     title : "UserId",
        //     //     data : 'userId'
        //     // }, {
        //     //     title : "Ip Address",
        //     //     data : 'ipAddress'
        //     // }
    
        //     // ]
        //     "ajax": {
        //         "type": "POST",
        //         "dataType": "json",
        //         "url": "/post",
        //         "data": function(d) {
        //             d.query_string = $("#textbox").val();
        //             d.database_type= $('input[name=database_type]:checked').val();
        //         },
        //         "dataSrc": ""
        //         // "success": function(data) {
        //         //     console.log(data)
        //         //     // $('#main').html(data.responseText);
        //         // }
        //     }

        // });
    })
});

function loadTable(data) {
    column_object = [];
    for (key in data[0]) {
        column_object.push({
            title: key,
            data: key
        })
    }

    $('.display-table').remove('#display-table');
    $('.display-table').html("<table id='display-table'></table>")

    $('#display-table').DataTable({
        bSort: false,
        data : data,
        // "bPaginate": false,
        bFilter: true,
        bSort: true,
        bInfo: true,
        columns: column_object,
    }
)}