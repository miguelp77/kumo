(function($){
  $(function(){

    $('.button-collapse').sideNav();
    // $('.parallax').parallax();

  }); // end of document ready
})(jQuery); // end of jQuery name space
  // params url
  function removeParam(key, sourceURL) {
      var rtn = sourceURL.split("?")[0],
          param,
          params_arr = [],
          queryString = (sourceURL.indexOf("?") !== -1) ? sourceURL.split("?")[1] : "";
      if (queryString !== "") {
          params_arr = queryString.split("&");
          for (var i = params_arr.length - 1; i >= 0; i -= 1) {
              param = params_arr[i].split("=")[0];
              if (param === key) {
                  params_arr.splice(i, 1);
              }
          }
          rtn = rtn + "?" + params_arr.join("&");
      }
      return rtn;
  }
  // end params
  var work_hours = function (s,e) {
    var i = 0;
    var idx = 0;
    var data = [];
    for (s; s <= e; s.setDate(s.getDate() + 1)) {
      console.log(s);
      var dato = s.toDateString();       
      // i = i +1;
      var day = s.getDay();
      var isWeekend = (day == 6) || (day == 0);
      // console.log(isWeekend);
      if(!isWeekend) {
        i = i + 8;
        data.push(dato);
      } 
    }
    return [i,data];
  }

  $( document ).ready(function() {

    $(".burger").on("click", function  () {

      $("#index-banner").toggleClass("index-bannerTop");
      $("#nav-mobile").toggleClass("show");
      $("#nav-mobile").toggle();
    });
  
  var select_start_date;
  var start_date = $('#start_date').pickadate({
    selectMonths: true, // Creates a dropdown to control month
    selectYears: 3, // Creates a dropdown of 15 years to control year,
    today: 'Hoy',
    clear: 'Limpiar',
    close: 'Ok',
    firstDay: 1,
    format: 'dd-mm-yyyy',
    formatSubmit: 'yyyy-mm-dd',
    closeOnSelect: true, // Close upon selecting a date,
    monthsFull: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
    monthsShort: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
    weekdaysFull: ['Domingo', 'Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado'],
    weekdaysShort: ['Dom', 'Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab'],
    showMonthsShort: true,
    hiddenName: true,
    onClose: function() {
      // console.log(start_date)
      var a = [];
      var s = start_date.pickadate('picker');
      select_start_date = s.get('select', 'yyyy-mm-dd');
      a = select_start_date.toString().split("-");
      var integers = a.map(function(x) {
        return parseInt(x,10);
      });
      integers[1] = integers[1] - 1; // los meses estan en base 0
      var e = end_date.pickadate('picker');
      e.set( 'min',integers);
    },

  });

  var end_date = $('#end_date').pickadate({
    selectMonths: true, // Creates a dropdown to control month
    selectYears: 3, // Creates a dropdown of 15 years to control year,
    today: 'Hoy',
    clear: 'Limpiar',
    close: 'Ok',
    firstDay: 1,
    format: 'dd-mm-yyyy',
    formatSubmit: 'yyyy-mm-dd',
    closeOnSelect: true, // Close upon selecting a date,
    monthsFull: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
    monthsShort: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
    weekdaysFull: ['Domingo', 'Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado'],
    weekdaysShort: ['Dom', 'Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab'],
    showMonthsShort: true,
    hiddenName: true,
    onClose: function() {
      var e = end_date.pickadate('picker');
      select_end_date = e.get('select', 'yyyy-mm-dd');
      var startDate = new Date(select_start_date);
      var endDate = new Date(select_end_date);
      // console.log(endDate - startDate);
      work_days = work_hours(startDate,endDate);
      wh = work_days[0]
      wd = work_days[1]
      console.log(work_days);
      $('#hours').val(wh);
      if(wh>8) {
        console.log("APPEND");
        $('#workdays').remove();
        $('#hours').closest( "div" ).append("<span class='badget light-blue accent-3' id='workdays'>" + " horas aprox</span>");
      }
      
      // for(var i=0;i < wd.length;i++){
      //   console.log(wd[i]);
      //   // $('#days').append('<li class="collection-item">' + 
      //   //     '<span class="title">' + wd[i] +'</span>' +
      //   //     '<p>' + $('#project').val() + '<br>' +
      //   //     $('#approver').val() + 
      //   //     '</p>' + 
      //   //     '</li>');
      //   $('#days > tbody:last-child').append('<tr>' + 
      //     '<td>' + wd[i] + '</td>' + 
      //     '<td>' + $('#project').val() + '</td>' + 
      //     '<td>' + $('#approver').val() + '</td>' + 
      //   '</tr>');

      // }
    }
  });  

  // Validation form
  $('#form').on('change', function(){
         if($('#project').val() != null && $('#approver').val() != null ){
           if($('#start_date').siblings('input').val() != "" && $('#end_date').siblings('input').val() != "" ){       
               console.log($('#start_date'));
               $('#submit').removeAttr('disabled');  
           } else {
             $('#submit').attr('disabled','disabled');
           }
         } else {
           $('#submit').attr('disabled','disabled');
         }
       });

  $('#check_all[type="checkbox"]+label').on('click', function(){
    if(!$("#check_all").prop('checked')){
      $("#check_all").prop('checked', true);
      $(".checkBoxClass").prop('checked', true);
    }else{
      $("#check_all").prop('checked', false);
      $(".checkBoxClass").prop('checked', false);
    }
  });


  $('select').material_select();

  $('select[name=project]').on('change', function(e){ 
    // TODO: Limpiar los dropdown
    $('select[name=approver]').material_select('destroy');
    $('select[name=hours_type]').material_select('destroy');


    // var selection = $(this).find("option:selected");
    // console.log(selection.data()); 
    var data = $(this).find("option:selected").data('id');
    var a = data;
    data = a.replace("[", "").replace("]", "").replace(/'/g,"");  
 
    var opts = data.split(',');
    $('#approver').children('option:not(:first)').remove();
    for(var i =0;i < opts.length; i++){
      $('#approver').append('<option value="'+opts[i]+'">'+opts[i]+'</option>');
    }
    var hours_type = $(this).find("option:selected").data("type");
     a = hours_type.replace("[", "").replace("]", "").replace(/'/g,"");
     opts  = a.split(',');
     $('#hours_type').children('option:not(:first)').remove();
     for(var i =0;i < opts.length; i++){
      $('#hours_type').append('<option value="'+opts[i]+'">'+opts[i]+'</option>');
      console.log(opts[i])
    }


    e.preventDefault(); 
    $('select[name=approver]').material_select();
    $('select[name=hours_type]').material_select();
  }); 


//BBULK Buttons
        $('ul.tabs').tabs('select_tab', 'tab_id');
   
        //Si estan todos los checkbox marcados y desmarcas uno, el checkbox_all se desactiva. 
        $('.checkBoxClass').on('click',function(){
          if ($('#check_all').is(':checked')){
            if ($('.checkBoxClass').is(':checked')) {
              $('#check_all').prop('checked', false);
            }
          }
        });

        //Activa o desactiva el boton de borrar imputaciones dependiendo de si el checkbox del header esta marcado o no
        $('#check_all[type="checkbox"]+label').on('click',function(){
          if($("#check_all").prop('checked')){
            document.getElementById("buttonDelete").removeAttribute("disabled");            
            document.getElementById("buttonSubmit").removeAttribute("disabled");            
            document.getElementById("buttonReject").removeAttribute("disabled");            
            document.getElementById("buttonApprove").removeAttribute("disabled");            
          } else {
            document.getElementById("buttonDelete").setAttribute("disabled","disabled");
            document.getElementById("buttonSubmit").setAttribute("disabled","disabled");
            document.getElementById("buttonReject").setAttribute("disabled","disabled");
            document.getElementById("buttonApprove").setAttribute("disabled","disabled");
          }
        });

        //activa o desactiva el boton de borrar imputaciones dependiendo de si hay alguna umputacion con el checkbox marcado.
        $('.checkBoxClass').on('change',function(){
          
          if($('.checkBoxClass').is(':checked')){
            document.getElementById("buttonDelete").removeAttribute("disabled");                    
            document.getElementById("buttonSubmit").removeAttribute("disabled");                    
            document.getElementById("buttonReject").removeAttribute("disabled");                    
            document.getElementById("buttonApprove").removeAttribute("disabled");                    
          } else {
            document.getElementById("buttonDelete").setAttribute("disabled","disabled");          
            document.getElementById("buttonSubmit").setAttribute("disabled","disabled");          
            document.getElementById("buttonReject").setAttribute("disabled","disabled");          
            document.getElementById("buttonApprove").setAttribute("disabled","disabled");          
          }
        });  

        arrRows = [];
        rowCount = 0;
        ids = []
        function courtain_show() {
          $('#preloader').css({display: "block"});
        }

        function courtain_hide() {
          $('#preloader').css({display: "none"});
        }
        // Bulk deletion 
        $('#buttonDelete').on('click', function() {
          $('.checkBoxClass').each(function(){
            // TODO: Check if array is empty

            rowCount++;
            if($(this).prop( "checked" )){
              var selected_id = $(this).attr('id');
              ids.push(selected_id);
            }
          });
          courtain_show();
          // Borrar todas las seleccionadas y recargar
          // TOODO: Alert message 
          $.getJSON($SCRIPT_ROOT + '/a/_delete_selection', { ids: JSON.stringify(ids) } )
            .done(function( data ) {
              // console.log( "JSON Data: " + data );
              window.location.reload(false);
            })
            .fail(function( jqxhr, textStatus, error ) {
              var err = textStatus + ", " + error;
              // console.log( "Request Failed: " + err );
              courtain_hide();
          });
        });
        // Bulk submit 
        $('#buttonSubmit').on('click', function(){

          $('.checkBoxClass').each(function(){
            rowCount++;

            if($(this).prop( "checked" )){
              var selected_id = $(this).attr('id');
              ids.push(selected_id);
            }
          });
          courtain_show();
          // Borrar todas las seleccionadas y recargar
          // TOODO: Alert message 
          $.getJSON($SCRIPT_ROOT + '/a/_submit_selection', { ids: JSON.stringify(ids) } )
            .done(function( data ) {
              // console.log( "JSON Data: " + data );
              window.location.reload(false);
            })
            .fail(function( jqxhr, textStatus, error ) {
              var err = textStatus + ", " + error;
              // console.log( "Request Failed: " + err );
              courtain_hide();

          });            
        });
        // Bulk buttonReject
        $('#buttonReject').on('click', function(){

          $('.checkBoxClass').each(function(){
            rowCount++;

            if($(this).prop( "checked" )){
              var selected_id = $(this).attr('id');
              ids.push(selected_id);
            }
          });
          courtain_show();
          // Borrar todas las seleccionadas y recargar
          // TOODO: Alert message 
          $.getJSON($SCRIPT_ROOT + '/a/_reject_selection', { ids: JSON.stringify(ids) } )
            .done(function( data ) {
              // console.log( "JSON Data: " + data );
              window.location.reload(false);
            })
            .fail(function( jqxhr, textStatus, error ) {
              var err = textStatus + ", " + error;
              console.log( "Request Failed: " + err );
              courtain_hide();
          });            
        });

        // Bulk buttonApprove
        $('#buttonApprove').on('click', function(){

          $('.checkBoxClass').each(function(){
            rowCount++;

            if($(this).prop( "checked" )){
              var selected_id = $(this).attr('id');
              ids.push(selected_id);
            }
          });
          courtain_show();

          // Borrar todas las seleccionadas y recargar
          // TOODO: Alert message 
          $.getJSON($SCRIPT_ROOT + '/a/_approve_selection', { ids: JSON.stringify(ids) } )
            .done(function( data ) {
              console.log( "JSON Data: " + data );
              window.location.reload(false);
            })
            .fail(function( jqxhr, textStatus, error ) {
              var err = textStatus + ", " + error;
              console.log( "Request Failed: " + err );
              courtain_hide();
          });            
        });

        // TABLE ORDER
        $("#table-allocations").tablesorter({headers: { 0: { sorter: false} }}); 
});
