PQitemtype='TextIndicator'

PQshortcut='Ctrl+E'

ZERO='0' #zero point label, leave '' for none.

def place_marks(PQText):
    ts=PQText.series
    fhighs,flows=get_fractals(ts)
    ehighs=highest_highs(fhighs,flows)
    elows=lowest_lows(fhighs,flows)
    lbls=label_waves(ehighs,elows)
    #for testing/debugging:
    # waves=labels_to_dict(lbls) 
    if (waves:=find_impulse_up(lbls,ts))==[]: waves=find_impulse_down(lbls,ts)
    def place(w):
        i=w['bar']
        if w['type']=="Up": pl=ts.highs[i]; yanch=1
        else: pl=ts.lows[i]; yanch=0
        txt=ZERO if w['wave']=='0' else w['wave']
        si=PQText.create_subitem("Text",values=(ts.times[i],pl), text=txt)
        si.set_anchor(x=0.5,y=yanch)
    if waves:
        for wave in waves:
            place(wave)
    else:
        tag=labels_to_dict(lbls)[-1]
        tag['wave']='EW'
        place(tag)

def get_fractals(ts, degree=2):
    highs = []
    lows = []
    for i in range(degree, len(ts.highs)-degree):
        if ts.highs[i]>max(ts.highs[i - degree:i]) and ts.highs[i]>max(ts.highs[i+1:i+degree+1]):
            highs.append((i,ts.highs[i]))
        if ts.lows[i]<min(ts.lows[i - degree:i]) and ts.lows[i]<min(ts.lows[i+1:i+degree+1]):
            lows.append((i,ts.lows[i]))
    return highs, lows

def highest_highs(tshighs, tslows):
    result = []
    current = []
    i = j = 0

    # if no tslow between the last tshigh and the end of the timeseries,
    # append dummy 0-value tslow at the end to ensure that the last highest high is not lost
    dummy_appended=False
    if tslows[-1][0]<=(lh:=tshighs[-1][0]):
        tslows.append((lh+1,0))
        dummy_appended=True

    while i < len(tshighs) and j < len(tslows):
        if tshighs[i][0] < tslows[j][0]:
            current.append(tshighs[i])
            i += 1
        else:
            if current:
                highest = (current[0][0], current[0][1])
                for high in current[1:]:
                    if high[1] > highest[1]:
                        highest = high
                result.append(highest)
                current = []
            j += 1
    if current:
        highest = (current[0][0], current[0][1])
        for high in current[1:]:
            if high[1] > highest[1]:
                highest = high
        result.append(highest)
    #drop the dummy on exit
    if dummy_appended: tslows.pop()
    return result

def lowest_lows(tshighs, tslows):
    result = []
    current = []
    i = j = 0

    # if no tshigh between the last tslow and the end of the timeseries,
    # append dummy 0-value tshigh at the end to ensure that the last lowest low is not lost
    dummy_appended=False
    if tshighs[-1][0]<=(ll:=tslows[-1][0]):
        tshighs.append((ll+1,0))
        dummy_appended=True

    while i < len(tshighs) and j < len(tslows):
        if tslows[j][0] < tshighs[i][0]:
            current.append(tslows[j])
            j += 1
        else:
            if current:
                lowest = (current[0][0], current[0][1])
                for low in current[1:]:
                    if low[1] < lowest[1]:
                        lowest = low
                result.append(lowest)
                current = []
            i += 1
    if current:
        lowest = (current[0][0], current[0][1])
        for low in current[1:]:
            if low[1] < lowest[1]:
                lowest = low
        result.append(lowest)
    #drop the dummy on exit
    if dummy_appended:tshighs.pop()
    return result

def label_waves(highs, lows):
    highs = [("Up", pos, val) for pos, val in highs]
    lows = [("Down", pos, val) for pos, val in lows]
    labels = highs + lows
    labels = sorted(labels, key=lambda x: x[1])
    
    new_labels = []
    i = 0
    while i < len(labels):
        if i == 0 or labels[i][0] != labels[i-1][0]:
            new_labels.append(labels[i])
        else:
            if labels[i][0] == "Up" and labels[i][2] >= labels[i-1][2]:
                new_labels.pop()
                new_labels.append(labels[i])
            elif labels[i][0] == "Down" and labels[i][2] <= labels[i-1][2]:
                new_labels.pop()
                new_labels.append(labels[i])
        i += 1
    return new_labels

def labels_to_dict(labels):
    lbls=[]
    for l in labels:
        lbls.append(dict(type=l[0],bar=l[1],value=l[2],wave=l[0]))
    return lbls

def find_impulse_up(lst,ts):
    waves = []
    #point 0 index in lst
    index0=None
    for i in range(len(lst) - 1, -1, -1):
        if lst[i][0] == 'Up':
            j = i - 1
            next_up = None
            while j >= 0 and lst[j][0] != 'Up':
                j -= 1
            if j >= 0:
                next_up = lst[j]
                if lst[i][2] > next_up[2]:
                    waves.append({"type": lst[i][0], "bar": lst[i][1], "value": lst[i][2], "wave": '5'})
                    k = i - 1
                    lowest_down = None
                    min_val = float("inf")
                    while k > j:
                        if lst[k][0] == "Down" and lst[k][2] < min_val:
                            min_val = lst[k][2]
                            lowest_down = lst[k]
                        k -= 1
                    if lowest_down:
                        waves.append({"type": lowest_down[0], "bar": lowest_down[1], "value": lowest_down[2], "wave": '4'})
                    waves.append({"type": next_up[0], "bar": next_up[1], "value": next_up[2], "wave": '3'})
                    k = j - 1
                    next_down = None
                    while k >= 0 and lst[k][0] != 'Down':
                        k -= 1
                    if k >= 0:
                        next_down = lst[k]
                        waves.append({"type": next_down[0], "bar": next_down[1], "value": next_down[2], "wave": '2'})
                        k -= 1
                        while k >= 0:
                            if lst[k][0] == 'Down' and lst[k][2] <= next_down[2]:
                                waves.append({"type": lst[k][0], "bar": lst[k][1], "value": lst[k][2], "wave": '0'})
                                index0=k
                                m = j - 1
                                highest_up = None
                                max_val = float("-inf")
                                while m > k:
                                    if lst[m][0] == 'Up' and lst[m][2] > max_val:
                                        max_val = lst[m][2]
                                        highest_up = lst[m]
                                    m -= 1
                                if highest_up:
                                    waves.append({"type": highest_up[0], "bar": highest_up[1], "value": highest_up[2], "wave": '1'})
                                break
                            k -= 1
                    break
    
    #impulse tests
    vals=[None]*6
    bars=[None]*6
    for w in waves:
        vals[(i:=int(w['wave']))]=w['value']
        bars[(i:=int(w['wave']))]=w['bar']
    for v in vals:
        if v is None:
            waves=[]
            break

    if waves:
        #waves 2 and 4 do not overlap
        max2=max(ts.highs[bars[1]:bars[2]+1])
        min4=min(ts.lows[bars[3]:bars[4]+1])
        if max2>=min4: waves=[]
        #wave 3 is not the shortest of 1,3 and 5
        if vals[3]-vals[2]< min(vals[1]-vals[0],vals[5]-vals[4]): waves=[]
        #ensure that point 0 is a local minimum
        for extr in reversed(lst[:index0]):
            if extr[0]=="Down":
                if extr[2]<vals[0]: waves=[]
                break
        #ensure no stop-out invalidation
        if min(ts.lows[bars[0]:])<vals[0]:waves=[]

    return waves

def find_impulse_down(lst,ts):
    waves = []
    #point 0 index in lst
    index0=None
    for i in range(len(lst) - 1, -1, -1):
        if lst[i][0] == 'Down':
            j = i - 1
            next_down = None
            while j >= 0 and lst[j][0] != 'Down':
                j -= 1
            if j >= 0:
                next_down = lst[j]
                if lst[i][2] < next_down[2]:
                    waves.append({"type": lst[i][0], "bar": lst[i][1], "value": lst[i][2], "wave": '5'})
                    k = i - 1
                    highest_up = None
                    max_val = float("-inf")
                    while k > j:
                        if lst[k][0] == "Up" and lst[k][2] > max_val:
                            max_val = lst[k][2]
                            highest_up = lst[k]
                        k -= 1
                    if highest_up:
                        waves.append({"type": highest_up[0], "bar": highest_up[1], "value": highest_up[2], "wave": '4'})
                    waves.append({"type": next_down[0], "bar": next_down[1], "value": next_down[2], "wave": '3'})
                    k = j - 1
                    next_up = None
                    while k >= 0 and lst[k][0] != 'Up':
                        k -= 1
                    if k >= 0:
                        next_up = lst[k]
                        waves.append({"type": next_up[0], "bar": next_up[1], "value": next_up[2], "wave": '2'})
                        k -= 1
                        while k >= 0:
                            if lst[k][0] == 'Up' and lst[k][2] >= next_up[2]:
                                waves.append({"type": lst[k][0], "bar": lst[k][1], "value": lst[k][2], "wave": '0'})
                                index0=k
                                m = j - 1
                                lowest_down = None
                                min_val = float("inf")
                                while m > k:
                                    if lst[m][0] == 'Down' and lst[m][2] < min_val:
                                        min_val = lst[m][2]
                                        lowest_down = lst[m]
                                    m -= 1
                                if lowest_down:
                                    waves.append({"type": lowest_down[0], "bar": lowest_down[1], "value": lowest_down[2], "wave": '1'})
                                break
                            k -= 1
                    break
    
    #impulse tests
    vals=[None]*6
    bars=[None]*6
    for w in waves:
        vals[(i:=int(w['wave']))]=w['value']
        bars[(i:=int(w['wave']))]=w['bar']
    for v in vals:
        if v is None:
            waves=[]
            break

    if waves:
        #waves 2 and 4 do not overlap
        min2=min(ts.lows[bars[1]:bars[2]+1])
        max4=max(ts.highs[bars[3]:bars[4]+1])
        if min2<=max4: waves=[]
        #wave 3 is not the shortest of 1,3 and 5
        if vals[2]-vals[3]< min(vals[0]-vals[1],vals[4]-vals[5]): waves=[]
        #ensure that point 0 is a local maximum
        for extr in reversed(lst[:index0]):
            if extr[0]=="Up":
                if extr[2]>vals[0]: waves=[]
                break
        #ensure no stop-out invalidation
        if max(ts.highs[bars[0]:])>vals[0]: waves=[]

    return waves

def remove_marks(PQtext):
    for si in list(PQtext.subitems):
        PQtext.remove_subitem(si)

def PQinitf(PQtext):
    place_marks(PQtext)
    PQtext.sigSeriesChanged.connect(PQupdatef)

def PQupdatef(PQtext):
    remove_marks(PQtext)
    place_marks(PQtext)