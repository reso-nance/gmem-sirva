$( document ).ready(function() {
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + '/home')  
    var connectedDevices = [];
    //~ var testModule = {name:"testModule", volumes:[25,50,75,100], IP:"10.0.0.42", midiNote:60, fileList:["testFile1.wav", "testFile2.wav", "testFile3.wav"], connected:true, lastSeen:"10/10/2019 09h23"}
    //~ var testModule2 = {name:"testModule2", volumes:[10,30,45,83], IP:"10.0.0.44", midiNote:53, fileList:["testFile1.wav", "testFile2.wav", "testFile3.wav"], connected:true, lastSeen:"10/10/2019 09h13"}
    //~ connectedDevices.push(testModule)
    //~ connectedDevices.push(testModule2)
    
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
 		if ($(parent_module).find( "li" ).hasClass("selectedwave"))
 		{
 			$(parent_module).find( "li" ).removeClass("selectedwave");
 			$(parent_module).find( "li" ).addClass("unselectedwave");
 			// set btn_play / stop active
 			$(parent_module).find( ".btn_play" ).removeClass("desactivated");
 			$(parent_module).find( ".btn_play" ).addClass("activated");
 		}

 		// add remove class selected on selection
 		$( this ).parent().removeClass("unselectedwave");
 		$( this ).parent().addClass("selectedwave");
 		// change alert
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
 	});	
    
    $(document).on('click', '#bplay', function(event) {
        const moduleName = $(this).attr('data-modulename');
        //~ const fileSelected = $("#"+moduleName+" .ui-module-details .wav-list ").find(".selectedwave .a")
        const fileSelected = $("#"+moduleName+" .selectedwave").children("a").text()
        console.log("playing file",fileSelected, "on module", moduleName);
        socket.emit("playFile", {hostname:moduleName, fileSelected:encodeURIComponent(fileSelected)});
    });
    
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
            $('.slider:[data-moduleName="'+data.hostname+'"]:[data-type="'+i.toString()+'"]').val(data.volumes[i]);
        }
    });
    
    // update fileList on server request
    socket.on('updateFileList', function(data) {
        console.log("update fileList :", data)
        updateFileList(data.hostname, data.fileList)
    });
        
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
        var statusList = $('<ul class="list-group statuslist" id="status-list">');
        connectedDevices.forEach(function(device){
            const disabled = (device.connected) ? "" : '"class="disabled" tabindex="-1"';
            deviceList.append('<li data-modulename="'+device.name+'"><a href="#" '+disabled+'>'+device.name+'</a></li>');
            statusList.append('<a href="#">'+device.status+'</a>');
        });
        deviceList.append('</ol>');
        statusList.append('</ul>');
        $("#devices-list").replaceWith(deviceList);
        $("#status-list").replaceWith(statusList);
        console.log("updated devices list :", connectedDevices);
    }
    
    function updateFileList(moduleName, fileList) {
        var fileListHTML = "";
        fileList.forEach(function(file){
            fileListHTML += '<li><a href=#>'+file+'</a></li>';
        });
        $("#"+moduleName+" .ui-module-details .wav-list ul").empty().append(fileListHTML);
    }        
        
});


function show_module(module){
    console.log("displaying module", module);
	// affichage
	if ( $( ".content #"+module.name ).length ) {
		$(".content #"+module.name).remove();
	} else
	{
		$(".content").append('<element class= ui-module-container id = '+module.name+'></element>');
		$("#"+module.name).append('<div class= ui-module-head></div>');
		$("#"+module.name+" .ui-module-head").append('<div class= ui-module-id></div>');
		$("#"+module.name+" .ui-module-head .ui-module-id").append('<div class="module_infos module-name"><h1>'+module.name+'</h1></div>');
		$("#"+module.name+" .ui-module-head .ui-module-id").append('<div class= module_infos><h3>IP '+module.IP+'</h3></div>');
		$("#"+module.name+" .ui-module-head .ui-module-id").append('<div class= module_infos id = midiinfo><h3>notemidi </h3></div>');
		$("#"+module.name+" .ui-module-head .ui-module-id").append('<div class= module_infos id = midinote><h3>'+module.midiNote+'</h3></div>');
		$("#"+module.name+" .ui-module-head .ui-module-id").append('<div class=btns_up></div>');
		$("#"+module.name+" .ui-module-head .ui-module-id .btns_up").append('<button class=btn id=bplay data-modulename="'+module.name+'"></button>');
		$("#"+module.name+" #bplay").addClass("btn_play desactivated statelist");
		$("#"+module.name+" .ui-module-head .ui-module-id .btns_up").append('<button class=btn id=bstop></button>');
		$("#"+module.name+" #bstop").addClass("btn_stop desactivated statelist");
		$("#"+module.name+" .ui-module-head .ui-module-id .btns_down").append('<button class=btn id=badd></button>');
		$("#"+module.name+" #badd").addClass("btn_add desactivated statelist");
		$("#"+module.name+" .ui-module-head .ui-module-id .btns_down").append('<button class=btn id=bdelete></button>');
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
		$("#"+module.name+" .ui-module-details").append('<div class=wav-list id=liste>');
		$("#"+module.name+" .ui-module-details .wav-list").append('<ul class=col2></ul>');
        var fileList = ""
        module.fileList.forEach(function(file){
            fileList += '<li><a href=#>'+file+'</a></li>';
        });
        $("#"+module.name+" .ui-module-details .wav-list ul").append(fileList);
		//~ $("#"+module.name+" .ui-module-details .wav-list ul").append('<li><a href='+"#"+'>Norirnmurcol.wav</a></li><li><a href='+"#"+'>Thalogcollam.wav</a></li><li><a href='+"#"+'>Hellborcil.wav</a></li><li><a href='+"#"+'>Nircullam.wav</a></li><li><a href='+"#"+'>Hocelnarlysnar.wav</a></li><li><a href='+"#"+'>Lushelllosgymcul.wav</a></li><li><a href='+"#"+'>Nirthoyrnlem.wav</a></li><li><a href='+"#"+'>Lusholys.wav</a></li><li><a href='+"#"+'>Selmercolthasel.wav</a></li><li><a href='+"#"+'>Mararnmer.wav</a></li><li><a href='+"#"+'>Hurgember.wav</a></li><li><a href='+"#"+'>Urnmarsyllo.wav</a></li>');
	}
}

//~ function show_module(mymodule){
	//~ // var index
	//~ var module_index = mymodule.index();
	//~ // get name
	//~ var module_name = mymodule.find("a").text();
	//~ // affichage
	//~ if ( $( ".content #"+module_name ).length ) {
		//~ $(".content #"+module_name).remove();
	//~ } else
	//~ {
		//~ $(".content").append('<element class= ui-module-container id = '+module_name+'></element>');
		//~ $("#"+module_name).append('<div class= ui-module-head></div>');
		//~ $("#"+module_name+" .ui-module-head").append('<div class= ui-module-id></div>');
		//~ $("#"+module_name+" .ui-module-head .ui-module-id").append('<div class= module_infos><h1>'+module_name+'</h1></div>');
		//~ $("#"+module_name+" .ui-module-head .ui-module-id").append('<div class= module_infos id = '+module_index+'><h3>'+module_name+' IPvar</h3></div>');
		//~ $("#"+module_name+" .ui-module-head .ui-module-id").append('<div class= module_infos id = midiinfo><h3>midinote </h3></div>');
		//~ $("#"+module_name+" .ui-module-head .ui-module-id").append('<div class= module_infos id = midinote><h3>11</h3></div>');
		//~ $("#"+module_name+" .ui-module-head .ui-module-id").append('<div class=btns_up></div>');
		//~ $("#"+module_name+" .ui-module-head .ui-module-id .btns_up").append('<button class=btn id=bplay></button>');
		//~ $("#"+module_name+" #bplay").addClass("btn_play desactivated statelist");
		//~ $("#"+module_name+" .ui-module-head .ui-module-id .btns_up").append('<button class=btn id=bstop></button>');
		//~ $("#"+module_name+" #bstop").addClass("btn_stop desactivated statelist");
		//~ $("#"+module_name+" .ui-module-head .ui-module-id .btns_down").append('<button class=btn id=badd></button>');
		//~ $("#"+module_name+" #badd").addClass("btn_add desactivated statelist");
		//~ $("#"+module_name+" .ui-module-head .ui-module-id .btns_down").append('<button class=btn id=bdelete></button>');
		//~ $("#"+module_name+" #bdelete").addClass("btn_delete desactivated statelist");
		//~ //
		//~ $("#"+module_name).append('<div class=ui-module-details></div>');
		//~ $("#"+module_name+" .ui-module-details").addClass("flex-container");
		//~ $("#"+module_name+" .ui-module-details").append('<div class=ui_btn id=module'+module_index+'></div>');
		//~ $("#"+module_name+" .ui-module-details .ui_btn").addClass("btn_unfold");
		//~ $("#"+module_name+" .ui-module-details").append('<div class=ui-module-vols id=volsin style=flex-grow:1>');
		//~ $("#"+module_name+" #volsin").append('<div class=bloc-vol id=audio_in'+module_index+' style=flex-grow:1><h2>micro in '+module_index+'</h2><input class=slider type=range min=0 max=100 /></div>');
		//~ $("#"+module_name+" #volsin").append('<div class=bloc-vol id=analog_in'+module_index+' style=flex-grow:1><h2>analog in '+module_index+'</h2><input class=slider type=range min=0 max=100 /></div>');
		//~ // volumes
		//~ $("#"+module_name+" .ui-module-details").append('<div class=ui-module-vols id=volsout style=flex-grow:1>');
		//~ $("#"+module_name+" #volsout").append('<div class=bloc-vol id=audio_in'+module_index+' style=flex-grow:1><h2>micro in '+module_index+'</h2><input class=slider type=range min=0 max=100 /></div>');
		//~ $("#"+module_name+" #volsout").append('<div class=bloc-vol id=analog_in'+module_index+' style=flex-grow:1><h2>analog in '+module_index+'</h2><input class=slider type=range min=0 max=100 /></div>');
		//~ // wave list
		//~ $("#"+module_name+" .ui-module-details").append('<div class=wav-list id=liste>');
		//~ $("#"+module_name+" .ui-module-details .wav-list").append('<ul class=col2></ul>');
		//~ $("#"+module_name+" .ui-module-details .wav-list ul").append('<li><a href='+"#"+'>Norirnmurcol.wav</a></li><li><a href='+"#"+'>Thalogcollam.wav</a></li><li><a href='+"#"+'>Hellborcil.wav</a></li><li><a href='+"#"+'>Nircullam.wav</a></li><li><a href='+"#"+'>Hocelnarlysnar.wav</a></li><li><a href='+"#"+'>Lushelllosgymcul.wav</a></li><li><a href='+"#"+'>Nirthoyrnlem.wav</a></li><li><a href='+"#"+'>Lusholys.wav</a></li><li><a href='+"#"+'>Selmercolthasel.wav</a></li><li><a href='+"#"+'>Mararnmer.wav</a></li><li><a href='+"#"+'>Hurgember.wav</a></li><li><a href='+"#"+'>Urnmarsyllo.wav</a></li>');
	//~ }
//~ }

/*
// parse a plain note number (ex "G#3") and return it's midi note number
function parsePlainNote(midiNote) {
    midiNote = midiNote.replace(/\s/g, ''); // remove spaces
    midiNote = midiNote.toUpperCase(); // convert to uppercase
    
    // generate an array regrouping every existing note name
    var noteNames = ["A","B","C","D","E","F","G"];
    const flats = ["D","E","G","A","B"];
    const sharps = ["C", "D", "F", "G", "A"];
    flats.forEach(function(note){noteNames.push(note+"B");})
    sharps.forEach(function(note){noteNames.push(note+"#");})
    noteNames.sort();
    console.log("notenames",noteNames);
    
    // separate input into numbers and other characters
    var chars = midiNote.slice(0, midiNote.search(/\d/));
    var numbers = parseInt(midiNote.replace(chars, ''));
    if (isNaN numbers) {
        console.log("don't forget the octave number (ex:'C#3')");
        return false;
    }
    else if (numbers < 0 || numbers > 9) {
        console.log("octave must be in 0~9 range");
        return false;
    }
    else if (!noteNames.includes(chars)) {
        console.log("unknown note "+chars);
        return false;
    }
    else if (chars in nameToNumber) return nameToNumber[chars]
}
*/
