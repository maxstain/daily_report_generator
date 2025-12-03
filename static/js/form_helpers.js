// Client-side form helper functions used by home.html
(function(window){
    const TIME_RE = /^\d{2}:\d{2}$/;

    function collectBookingGroups(){
        const groups = Array.from(document.querySelectorAll('.booking-row'));
        const arr = [];
        groups.forEach(function(g){
            const remote = (g.querySelector('.bk-remote') && g.querySelector('.bk-remote').value.trim()) || '';
            const start = (g.querySelector('.bk-start') && g.querySelector('.bk-start').value.trim()) || '';
            const end = (g.querySelector('.bk-end') && g.querySelector('.bk-end').value.trim()) || '';
            arr.push({remote, start, end});
        });
        return arr;
    }

    function collectTeGroups(){
        const groups = Array.from(document.querySelectorAll('.te-group'));
        const arr = [];
        groups.forEach(function(g){
            const id = (g.querySelector('.te-id') && g.querySelector('.te-id').value.trim()) || '';
            const summary = (g.querySelector('.te-summary') && g.querySelector('.te-summary').value.trim()) || '';
            const testsText = (g.querySelector('.te-tests') && g.querySelector('.te-tests').value.trim()) || '';
            const tests = testsText ? testsText.split(/\r?\n/).map(s=>s.trim()).filter(Boolean) : [];
            arr.push({id, summary, tests});
        });
        return arr;
    }

    function validateTimeFormat(time){
        if(!time) return true; // allow empty
        return TIME_RE.test(time);
    }

    function generatePreviewText(bookings, executions){
        // return a compact readable preview
        let out = '';
        out += 'Bookings:\n';
        if(!bookings || bookings.length===0) out += '  (none)\n';
        else bookings.forEach(function(b,i){
            const rem = b.remote || '';
            out += `  ${i+1}. ${rem} (${b.start || '--'} - ${b.end || '--'})\n`;
        });
        out += '\nExecutions:\n';
        if(!executions || executions.length===0) out += '  (none)\n';
        else executions.forEach(function(ex,i){
            out += `  ${i+1}. ${ex.id} - ${ex.summary || ''}\n`;
            if(ex.tests && ex.tests.length>0){
                ex.tests.forEach(function(t){ out += `      * ${t}\n`; });
            }
        });
        return out;
    }

    // Expose
    window.FormHelpers = {
        collectBookingGroups,
        collectTeGroups,
        validateTimeFormat,
        generatePreviewText
    };
})(window);

