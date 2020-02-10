$( document ).ready(function() {
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + '/home')  
    var connectedDevices = [];
    var testModule = {name:"testModule", volumes:[25,50,75,100], IP:"10.0.0.42", midiNote:60,status:'connecté', fileList:["testFile1.wav", "testFile2.wav", "testFile3.wav"], connected:true, lastSeen:"10/10/2019 09h23"}
    var testModule2 = {name:"testModule2", volumes:[10,30,45,83], IP:"10.0.0.44", midiNote:53, status:'non-connecté',fileList:["testFile1.wav", "testFile2.wav", "testFile3.wav"], connected:false, lastSeen:"10/10/2019 09h13"}
    connectedDevices.push(testModule);
    connectedDevices.push(testModule2);
    $("#wavDispatch").hide()
    // pour test !!!
    updateDeviceList();
    
    // replace the midinote by an input tag
    $(document).on('click', '#midinote', function(event) {
        const hostname = ($(event.target).children('h3').text());
        var original_text = $(this).text();
        var new_input = $('<input class="midinote-editor" id="'+hostname+'" data-original="'+original_text+'">');
        new_input.val(original_text);
        $(this).replaceWith(new_input);
        new_input.focus();
    });
    
    // Replace the input tag by a <div> and send the new name to the server when focus is lost
    $(document).on('blur', '.midinote-editor', function(event) {
        var new_input = $(this).val();
        const hostname = $(this).attr('id');
        const originalText = $(this).attr('data-original');
        var updated_text = $('<div class="module_infos" id="midinote">');
        const midiNote = getMidiNoteNumber(hostname, new_input);
        // if the entered midi note is valid, get it's number and send it to the server
        if (midiNote) {
            updated_text.html('<h3>'+new_input+'</h3>');
            socket.emit("midiNoteChanged", {hostname:encodeURIComponent(hostname), midinote:midiNote});
        }
        else updated_text.html('<h3>'+originalText+'</h3>');
        $(this).replaceWith(updated_text);
	});
    
    // replace the hostname by an input tag
    $(document).on('click', '.module-name', function(event) {
        const hostname = ($(event.target).text());
        var original_text = $(this).text();
        var new_input = $('<input class="modulename-editor" id="'+hostname+'">');
        new_input.append("<h1>");
        new_input.val(original_text);
        new_input.append("</h1>");
        $(this).replaceWith(new_input);
        new_input.focus();
    });
    
    // Replace the input tag by a <div> and send the new name to the server when focus is lost
    $(document).on('blur', '.modulename-editor', function(event) {
        var new_input = $(this).val();
        const hostname = $(this).attr('id');
        var updated_text = $('<div class="module_infos module-name">');
        const newHostname = getValidatedHostname(new_input);
        updated_text.html('<h1>'+newHostname+'</h1>');
        if (newHostname != hostname) {
            socket.emit("hostnameChanged", {hostname:encodeURIComponent(hostname), newHostname:newHostname})
        }
        $(this).replaceWith(updated_text);
	});

	// UNFOLD MODULE /////////////////////////////////////////////////
	$(document).on('click', '.btn_fold', function(event) {
	 	// change bg image ref
	 	$(this).removeClass("btn_fold").addClass("btn_unfold");
	 	//
	 	var parent_module = ( $(this).closest('.ui-module-container'));
	 	$(parent_module).css("height", 134);
	});
	// FOLD MODULE /////////////////////////////////////////////////
	$(document).on('click', '.btn_unfold', function(event) {
 		// change bg image ref
	 	$(this).removeClass("btn_unfold").addClass("btn_fold");
	 	//
	 	var parent_module = ( $(this).closest('.ui-module-container'));
	 	$(parent_module).css("height", 272);
	});	
	// SELECT FICHIER AUDIO
	$(document).on('click', '.col2 li a', function(event) {
		var parent_module = ( $(this).closest('.ui-module-container'));
 		// remove class selected for all list
 		$(this).parents('ul').children('li').removeClass("selectedwave");
        $(this).parent().addClass("selectedwave");
        // activate btns functions remove play delete
        parent_module.find('.btn_delete').css("opacity", "0.7");

        //alert(file_name);

 	});	
        
	// create module blocks when their <li> is clicked
	$(document).on('click', '.list-group li', function(event) {
        const moduleName = $(this).attr('data-modulename');
        const module = connectedDevices.filter(function (mod) {return mod.name === moduleName});
		if (module.length == 1) show_module(module[0]);
 	});	

	// notify the server of any slider change
    $(document).on('change', '.slider', function(event) {
        const moduleName = $(this).attr("data-moduleName");
        const value = parseInt($(this).val());
        const index = parseInt($(this).attr("data-type"));
        connectedDevices.forEach(function(module) {
            if (module.name === moduleName) {
                module.volumes[index] = value;
                socket.emit("volChanged", {hostname:encodeURIComponent(moduleName), index:index, volume:value});
            }
        });
    });
    
    // file upload
	$(document).on('change', '.upload', function(event) {
        $(this).closest('form').submit() //autosubmit the file upload form 
        console.log("submitted form",$(this).closest('form'))
     });

     
     $(document).on('click', '#modalSend', function(event){
        var clientList = [];
        console.log( $('#wavDispatchList'))
        $('#wavDispatchList input:checked').each(function() {
            clientList.push($(this).attr('data-moduleName'));
        });
        const filename = $("#wavDispatchName").text();
        console.log("dispatching", filename, "file to", clientList);
        socket.emit("dispatchFileToClients", {"filename":filename, "clientList":clientList});
     });

    $(document).on('click', '#bplay', function(event) {
        const moduleName = $(this).attr('data-modulename');
        //~ const fileSelected = $("#"+moduleName+" .ui-module-details .wav-list ").find(".selectedwave .a")
        const fileSelected = $("#"+moduleName+" .selectedwave").children("a").text()
        console.log("playing file",fileSelected, "on module", moduleName);
        socket.emit("playFile", {hostname:moduleName, fileSelected:encodeURIComponent(fileSelected)});
    });

    $(document).on('click', '#bstop', function(event) {
        const moduleName = $(this).attr('data-modulename');
        console.log("stop playing wav on module", moduleName);
        socket.emit("stopFile", moduleName);
    });

    $(document).on('click', '#bdelete', function(event) {
        const moduleName = $(this).attr('data-modulename');
        //~ const fileSelected = $("#"+moduleName+" .ui-module-details .wav-list ").find(".selectedwave .a")
        const fileSelected = $("#"+moduleName+" .selectedwave").children("a").text()
        console.log("deleting file",fileSelected, "on module", moduleName);
        socket.emit("deleteFile", {hostname:moduleName, fileSelected:encodeURIComponent(fileSelected)});
    });

    $(document).on('click', ".btn_refresh", function(event){
        console.log("refreshing known device list on the server");
        socket.emit("refreshClients");
    })

    $(document).on('click', ".btn_power", function(event){
        console.log("bye !");
        socket.emit("shutdown");
    })
    // update connected devices on server request
    socket.on('deviceList', function(data) {
        connectedDevices = Object.values(data);
        updateDeviceList();
    });
    
    // update sliders on server request
    socket.on('refreshVolumes', function(data) {
        console.log("update volumes :", data)
        const devIndex = connectedDevices.findIndex( mod => mod.name == data.hostname);
        connectedDevices[devIndex].volumes = data.volumes;
        for (var i=0; i<4; i++){
            $('.slider [data-moduleName="'+data.hostname+'"] [data-type="'+i.toString()+'"]').val(data.volumes[i]);
        }
    });
    
    // update fileList on server request
    socket.on('updateFileList', function(data) {
        console.log("update fileList :", data)
        updateFileList(data.hostname, data.fileList)
    });

    // open modal when a wav file is received on the server side
    socket.on('uploadSuccessful', function(filename) {
        console.log("upload successful :", filename, "opening modal...")
        // updating modal content
        var deviceList = $('<ul id="wavDispatchList">');
        connectedDevices.forEach(function(device){
            deviceList.append('<li class="checkbox moduleslist"><label data-moduleName="'+device.name+'"><input type="checkbox" value="" checked data-moduleName="'+device.name+'">'+device.name+'</label></li>');
        })
        deviceList.append("</ol>");
        $("#wavDispatchList").replaceWith(deviceList);
        $("#wavDispatchName").text(filename);
        $("#wavDispatch").modal();
    });
    
    socket.on("successfullDispatch", function(data){
        console.log("successfully dispatched", data.filename, "to", data.hostname);
        if (data.filename == $("#wavDispatchName").text()) {
            $('#wavDispatchList label[data-moduleName="'+data.hostname+'"] input').hide();
            $('#wavDispatchList label[data-moduleName="'+data.hostname+'"]').css('color', 'green');
            $('#wavDispatchList input[data-moduleName="'+data.hostname+'"]').attr("disabled", true);
        }
    })    

    socket.on("dispatchFailed", function(data){
        console.log("error dispatching", data.filename, "to", data.hostname);
        if (data.filename == $("#wavDispatchName").text()) {
            console.log("selected label :",$('"#wavDispatchList label[data-moduleName='+data.hostname+']"'));
            $('"#wavDispatchList label[data-moduleName='+data.hostname+']"').css('color', 'red');
        }
    })

    // returns a midi note number for the user-inputted text in the midinote field
    function getMidiNoteNumber(hostname, midiNote) {
        // try to parse an int (ex "63")
        const midiNoteNumber = parseInt(midiNote)
        if (! isNaN (midiNoteNumber)) {
            if (midiNoteNumber >= 12 && midiNoteNumber <= 127) {
                if (isUnique(hostname, midiNoteNumber)) return midiNoteNumber;
                else return false;
            }
            else {
                console.log("midi note not in range 12~127");
                return false;
            }
        }
        // try to parse a note name (ex "G#3")
        else {
            const midiNoteNumber = parsePlainNote(midiNote);
            if (midiNoteNumber && isUnique(hostname, midiNoteNumber)) return midiNoteNumber
            else return false;
        }
    }

    // check if a midinote is already assigned to another device
    function isUnique(hostname, midiNote) {
        for (var i=0; i<connectedDevices.length; i++) {
            if (connectedDevices[i].midiNote === midiNote && connectedDevices[i].hostname != hostname) {
                console.log("this midi note is already in use");
                return false;
            }
        }
        return true;
    }

    // parses a plain note number (ex "G#3") and return it's midi note number
    function parsePlainNote(midiNote) {
        // this object contain every note and number there is (previously generated with python)
        //const nameToNumber = {'C0': 12, 'C#0': 13, 'Db0': 13, 'D0': 14, 'D#0': 15, 'Eb0': 15, 'E0': 16, 'F0': 17, 'F#0': 18, 'Gb0': 18, 'G0': 19, 'G#0': 20, 'Ab0': 20, 'C9': 120, 'C#9': 121, 'Db9': 121, 'D9': 122, 'D#9': 123, 'Eb9': 123, 'E9': 124, 'F9': 125, 'F#9': 126, 'Gb9': 126, 'G9': 127, 'A0': 21, 'A#0': 22, 'Bb0': 22, 'B0': 23, 'C1': 24, 'C#1': 25, 'Db1': 25, 'D1': 26, 'D#1': 27, 'Eb1': 27, 'E1': 28, 'F1': 29, 'F#1': 30, 'Gb1': 30, 'G1': 31, 'G#1': 32, 'Ab1': 32, 'A1': 33, 'A#1': 34, 'Bb1': 34, 'B1': 35, 'C2': 36, 'C#2': 37, 'Db2': 37, 'D2': 38, 'D#2': 39, 'Eb2': 39, 'E2': 40, 'F2': 41, 'F#2': 42, 'Gb2': 42, 'G2': 43, 'G#2': 44, 'Ab2': 44, 'A2': 45, 'A#2': 46, 'Bb2': 46, 'B2': 47, 'C3': 48, 'C#3': 49, 'Db3': 49, 'D3': 50, 'D#3': 51, 'Eb3': 51, 'E3': 52, 'F3': 53, 'F#3': 54, 'Gb3': 54, 'G3': 55, 'G#3': 56, 'Ab3': 56, 'A3': 57, 'A#3': 58, 'Bb3': 58, 'B3': 59, 'C4': 60, 'C#4': 61, 'Db4': 61, 'D4': 62, 'D#4': 63, 'Eb4': 63, 'E4': 64, 'F4': 65, 'F#4': 66, 'Gb4': 66, 'G4': 67, 'G#4': 68, 'Ab4': 68, 'A4': 69, 'A#4': 70, 'Bb4': 70, 'B4': 71, 'C5': 72, 'C#5': 73, 'Db5': 73, 'D5': 74, 'D#5': 75, 'Eb5': 75, 'E5': 76, 'F5': 77, 'F#5': 78, 'Gb5': 78, 'G5': 79, 'G#5': 80, 'Ab5': 80, 'A5': 81, 'A#5': 82, 'Bb5': 82, 'B5': 83, 'C6': 84, 'C#6': 85, 'Db6': 85, 'D6': 86, 'D#6': 87, 'Eb6': 87, 'E6': 88, 'F6': 89, 'F#6': 90, 'Gb6': 90, 'G6': 91, 'G#6': 92, 'Ab6': 92, 'A6': 93, 'A#6': 94, 'Bb6': 94, 'B6': 95, 'C7': 96, 'C#7': 97, 'Db7': 97, 'D7': 98, 'D#7': 99, 'Eb7': 99, 'E7': 100, 'F7': 101, 'F#7': 102, 'Gb7': 102, 'G7': 103, 'G#7': 104, 'Ab7': 104, 'A7': 105, 'A#7': 106, 'Bb7': 106, 'B7': 107, 'C8': 108, 'C#8': 109, 'Db8': 109, 'D8': 110, 'D#8': 111, 'Eb8': 111, 'E8': 112, 'F8': 113, 'F#8': 114, 'Gb8': 114, 'G8': 115, 'G#8': 116, 'Ab8': 116, 'A8': 117, 'A#8': 118, 'Bb8': 118, 'B8': 119};
        const nameToNumber = {'C0': 12, 'C#0': 13, 'DB0': 13, 'D0': 14, 'D#0': 15, 'EB0': 15, 'E0': 16, 'F0': 17, 'F#0': 18, 'GB0': 18, 'G0': 19, 'G#0': 20, 'AB0': 20, 'C9': 120, 'C#9': 121, 'DB9': 121, 'D9': 122, 'D#9': 123, 'EB9': 123, 'E9': 124, 'F9': 125, 'F#9': 126, 'GB9': 126, 'G9': 127, 'A0': 21, 'A#0': 22, 'BB0': 22, 'B0': 23, 'C1': 24, 'C#1': 25, 'DB1': 25, 'D1': 26, 'D#1': 27, 'EB1': 27, 'E1': 28, 'F1': 29, 'F#1': 30, 'GB1': 30, 'G1': 31, 'G#1': 32, 'AB1': 32, 'A1': 33, 'A#1': 34, 'BB1': 34, 'B1': 35, 'C2': 36, 'C#2': 37, 'DB2': 37, 'D2': 38, 'D#2': 39, 'EB2': 39, 'E2': 40, 'F2': 41, 'F#2': 42, 'GB2': 42, 'G2': 43, 'G#2': 44, 'AB2': 44, 'A2': 45, 'A#2': 46, 'BB2': 46, 'B2': 47, 'C3': 48, 'C#3': 49, 'DB3': 49, 'D3': 50, 'D#3': 51, 'EB3': 51, 'E3': 52, 'F3': 53, 'F#3': 54, 'GB3': 54, 'G3': 55, 'G#3': 56, 'AB3': 56, 'A3': 57, 'A#3': 58, 'BB3': 58, 'B3': 59, 'C4': 60, 'C#4': 61, 'DB4': 61, 'D4': 62, 'D#4': 63, 'EB4': 63, 'E4': 64, 'F4': 65, 'F#4': 66, 'GB4': 66, 'G4': 67, 'G#4': 68, 'AB4': 68, 'A4': 69, 'A#4': 70, 'BB4': 70, 'B4': 71, 'C5': 72, 'C#5': 73, 'DB5': 73, 'D5': 74, 'D#5': 75, 'EB5': 75, 'E5': 76, 'F5': 77, 'F#5': 78, 'GB5': 78, 'G5': 79, 'G#5': 80, 'AB5': 80, 'A5': 81, 'A#5': 82, 'BB5': 82, 'B5': 83, 'C6': 84, 'C#6': 85, 'DB6': 85, 'D6': 86, 'D#6': 87, 'EB6': 87, 'E6': 88, 'F6': 89, 'F#6': 90, 'GB6': 90, 'G6': 91, 'G#6': 92, 'AB6': 92, 'A6': 93, 'A#6': 94, 'BB6': 94, 'B6': 95, 'C7': 96, 'C#7': 97, 'DB7': 97, 'D7': 98, 'D#7': 99, 'EB7': 99, 'E7': 100, 'F7': 101, 'F#7': 102, 'GB7': 102, 'G7': 103, 'G#7': 104, 'AB7': 104, 'A7': 105, 'A#7': 106, 'BB7': 106, 'B7': 107, 'C8': 108, 'C#8': 109, 'DB8': 109, 'D8': 110, 'D#8': 111, 'EB8': 111, 'E8': 112, 'F8': 113, 'F#8': 114, 'GB8': 114, 'G8': 115, 'G#8': 116, 'AB8': 116, 'A8': 117, 'A#8': 118, 'BB8': 118, 'B8': 119};
        midiNote = midiNote.replace(/\s/g, ''); // remove spaces
        midiNote = midiNote.toUpperCase(); // convert to uppercase
        if (midiNote in nameToNumber) return nameToNumber[midiNote];
        else return false;
    }
    
    function getValidatedHostname(hostname){
        hostname = hostname.replace(/\s/g, '-'); // replace spaces with hyphens
        hostname = hostname.normalize("NFD").replace(/[\u0300-\u036f]/g, ""); // remove diacritics from unicode
        hostname = hostname.replace(/[^a-zA-Z0-9-]/g,''); // remove the remaining special chars
        if (hostname.length > 62) hostname = hostname.slice(0, 62); // max 63 characters
        hostname = hostname.replace(/^\-/, ""); // remove the first hyphen if the hostname begins with an hyphen
        return hostname;
    }
    
    function updateDeviceList(){
        var deviceList = $('<ol class="list-group cachelist" id="devices-list">');
        //var statusList = $('<ul class="list-group statuslist" id="status-list">');
        connectedDevices.forEach(function(device){
            const disabled = (device.connected) ? "" : '"class="disabled" tabindex="-1"';
            deviceList.append('<li data-modulename="'+device.name+'"><a href="#" '+disabled+'>'+device.name+'</a><span class=statuslist> :: '+device.status+'</span></li>');
            //
        });
        deviceList.append('</ol>');
        //statusList.append('</ul>');
        $("#devices-list").replaceWith(deviceList);
        //$("#status-list").replaceWith(statusList);
        console.log("updated devices list :", connectedDevices);
    }
    
    function updateFileList(moduleName, fileList) {
        var fileListHTML = "";
        fileList.forEach(function(file){
            fileListHTML += '<li><a href=#>'+file+'</a></li>';
        });
        console.log($("#"+moduleName+" .ui-module-details .wav-list ul"));
        $("#"+moduleName+" .ui-module-details .wav-list ul").empty().append(fileListHTML);
        console.log($("#"+moduleName+"wavlist"));
    }

    function displayMidiFiles(midiFiles){
        var midiFilesHTML = "";
        midiFiles.forEach(function(file){
            console.log("adding midi file", file)
            midiFilesHTML += '<h3>'+file+'<h3><button type="button" class="btn btn-primary" id="midiDel" name="'+file+'">suppr</button></li>';
        });
        console.log("dbg html", midiFilesHTML);
        $("#midiFileList").html(midiFilesHTML);
};
        

function show_module(module){
    console.log("displaying module", module);
	// affichage
	if ( $( ".ContentRight #"+module.name ).length ) {
		$(".ContentRight #"+module.name).remove();
	} else
	{
		$(".ContentRight").append('<element class= ui-module-container id = '+module.name+'></element>');
		$("#"+module.name).append('<div class= ui-module-head></div>');
		$("#"+module.name+" .ui-module-head").append('<div class= ui-module-id></div>');
		$("#"+module.name+" .ui-module-head .ui-module-id").append('<div class="module_infos module-name"><h1>'+module.name+'</h1></div>');
		$("#"+module.name+" .ui-module-head .ui-module-id").append('<div class= module_infos><h3>IP '+module.IP+'</h3></div>');
		$("#"+module.name+" .ui-module-head .ui-module-id").append('<div class= module_infos id = midiinfo><h3>notemidi </h3></div>');
		$("#"+module.name+" .ui-module-head .ui-module-id").append('<div class= module_infos id = midinote><h3>'+module.midiNote+'</h3></div>');
	       // btns play stop
    	$("#"+module.name+" .ui-module-head .ui-module-id").append('<div class=btns_up></div>');
		$("#"+module.name+" .ui-module-head .ui-module-id .btns_up").append('<button class=btn id=bplay data-modulename="'+module.name+'"></button>');
		$("#"+module.name+" #bplay").addClass("btn_play desactivated statelist");
		$("#"+module.name+" .ui-module-head .ui-module-id .btns_up").append('<button class=btn id=bstop data-modulename="'+module.name+'"></button>');
		$("#"+module.name+" #bstop").addClass("btn_stop desactivated statelist");
        // btns add delete
        $("#"+module.name+" .ui-module-head .ui-module-id").append('<div class=btns_down></div>');
        //$("#"+module.name+" #badd").addClass("btn_add desactivated statelist");
		$("#"+module.name+" .ui-module-head .ui-module-id .btns_down").append('<button class=btn id="bdelete" data-modulename="'+module.name+'"></button>');
		$("#"+module.name+" #bdelete").addClass("btn_delete desactivated statelist");
		//
		$("#"+module.name).append('<div class=ui-module-details></div>');
		$("#"+module.name+" .ui-module-details").addClass("flex-container");
		$("#"+module.name+" .ui-module-details").append('<div class=ui_btn id=module'+module.name+'></div>');
		$("#"+module.name+" .ui-module-details .ui_btn").addClass("btn_unfold");
		$("#"+module.name+" .ui-module-details").append('<div class="ui-module-vols volsin" style="flex-grow:1">');
        // for sliders, data-type are ints representing the index of the volume in module.volumes (Mic:0, AnalogIN:1, Transducer:2, AnalogOUT:3)
		$("#"+module.name+" .volsin").append('<div class="bloc-vol" style="flex-grow:1"><h2>micro in </h2><input class="slider" type="range" min=0 max=100 value='+module.volumes[0]+' data-type=0 data-moduleName="'+module.name+'" /></div>');
		$("#"+module.name+" .volsin").append('<div class="bloc-vol" style="flex-grow:1"><h2>analog in </h2><input class="slider" type="range" min=0 max=100 value='+module.volumes[1]+' data-type=1 data-moduleName="'+module.name+'" /></div>');
		// volumes
		$("#"+module.name+" .ui-module-details").append('<div class="ui-module-vols volsout" style="flex-grow:1">');
		$("#"+module.name+" .volsout").append('<div class="bloc-vol" style=flex-grow:1><h2>transducteur out</h2><input class="slider" type="range" min=0 max=100 value='+module.volumes[2]+' data-type=2 data-moduleName="'+module.name+'" /></div>');
		$("#"+module.name+" .volsout").append('<div class=bloc-vol style=flex-grow:1><h2>analog in </h2><input class="slider" type="range" min=0 max=100 value='+module.volumes[3]+' data-type=3 data-moduleName="'+module.name+'" /></div>');
		// wave list
		$("#"+module.name+" .ui-module-details").append('<div class="wav-list" id="'+module.name+'wavlist">');
		$("#"+module.name+" .ui-module-details .wav-list").append('<ul class="col2"></ul>');
        var fileList = "";
        module.fileList.forEach(function(file){
            fileList += '<li><a href=#>'+file+'</a></li>';
        });
        $("#"+module.name+" .ui-module-details .wav-list ul").append(fileList);
		//~ $("#"+module.name+" .ui-module-details .wav-list ul").append('<li><a href='+"#"+'>Norirnmurcol.wav</a></li><li><a href='+"#"+'>Thalogcollam.wav</a></li><li><a href='+"#"+'>Hellborcil.wav</a></li><li><a href='+"#"+'>Nircullam.wav</a></li><li><a href='+"#"+'>Hocelnarlysnar.wav</a></li><li><a href='+"#"+'>Lushelllosgymcul.wav</a></li><li><a href='+"#"+'>Nirthoyrnlem.wav</a></li><li><a href='+"#"+'>Lusholys.wav</a></li><li><a href='+"#"+'>Selmercolthasel.wav</a></li><li><a href='+"#"+'>Mararnmer.wav</a></li><li><a href='+"#"+'>Hurgember.wav</a></li><li><a href='+"#"+'>Urnmarsyllo.wav</a></li>');
	}
}
});