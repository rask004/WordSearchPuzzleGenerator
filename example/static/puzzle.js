const CONTAINER_PUZZLE_CLASS = `puzzle-container`
const CONTAINER_WORDLIST_CLASS = `wordlist-container`
const CONTAINER_FOOTER_CLASS = `footer`
const AREA_CLASS = `area`
const CLICKHIGHLIGHT_CLASS = `area-highlight`
const WORD_FOUND_CLASS = `found`

const selectSequence = []
const sourceCoords = { x: -1, y: -1 }
const wordColors = []
let finished = false

const containerPuzzle = document.querySelector(`.${CONTAINER_PUZZLE_CLASS}`)
const containerWordlist = document.querySelector(`.${CONTAINER_WORDLIST_CLASS}`)
const containerFooter = document.querySelector(`.${CONTAINER_FOOTER_CLASS}`)
const documentStyleCustom = document.querySelector(`style`)

const CONTAINER_WIDTH = getComputedStyle(containerPuzzle).gridTemplateColumns.split(" ").length
const CONTAINER_HEIGHT = getComputedStyle(containerPuzzle).gridTemplateRows.split(" ").length


const randomColorCode = (a, b) => (parseInt((Math.random() * Math.abs(b - a)) + a)).toString(16).toUpperCase()


const zPadColorCode = (a, b, l) => {
    let code = randomColorCode(a, b)
    while (code.length < l) {
        code = `0${code}`
    }
    return code
}


const getColorCode = () => {
    const red = zPadColorCode(128, 255, 2)
    const green = zPadColorCode(0, 217, 2)
    const blue = zPadColorCode(50, 150, 2)

    return `#${red}${green}${blue}`

}

const changeTextColor = (e) => {
    e.style.color = `white`
}

const resetTextColor = (e) => {
    e.style.color = ""
}

const addHighlight = (e) => {
    e.style.backgroundColor = wordColors[wordColors.length - 1]
    changeTextColor(e)
}

const removeHighlight = (e) => {
    e.style.backgroundColor = ""
    resetTextColor(e)
}

const clickHighlight = (e) => {
    if (finished) {
        return
    }
    let highlightElement = e.target
    if (highlightElement.tagName === "SPAN") {
        highlightElement = highlightElement.parentElement
    }
    addHighlight(highlightElement)
    selectSequence.push(highlightElement)
    const container = highlightElement.parentElement
    const source_ndx = Array.from(container.children).indexOf(highlightElement)
    sourceCoords.x = source_ndx % CONTAINER_WIDTH
    sourceCoords.y = parseInt(source_ndx / CONTAINER_WIDTH)
}

const removeAllHighlightExceptFirstElement = () => {
    for (let i = selectSequence.length - 1; i > 0; i--) {
        removeHighlight(selectSequence[i])
    }
    selectSequence.splice(1, selectSequence.length)
}

const clickDragOver = (e) => {
    if (finished) {
        return
    }
    if (e.buttons && selectSequence.length > 0) {
        const targetArea = e.target.parentElement
        if (selectSequence[0] != targetArea) {
            const targetNdx = Array.from(containerPuzzle.children).indexOf(targetArea)
            const targetCoords = { x: targetNdx % CONTAINER_WIDTH, y: parseInt(targetNdx / CONTAINER_WIDTH) }
            const isLine = targetCoords.x === sourceCoords.x || targetCoords.y === sourceCoords.y || Math.abs(targetCoords.x - sourceCoords.x) === Math.abs(targetCoords.y - sourceCoords.y)
            // console.log(targetCoords, sourceCoords, isLine)
            if (isLine) {
                const affectedElements = []
                const step = { x: 0, y: 0 }
                if (targetCoords.x === sourceCoords.x) {
                    step.y = (targetCoords.y - sourceCoords.y) / Math.abs(targetCoords.y - sourceCoords.y)
                } else if (targetCoords.y === sourceCoords.y) {
                    step.x = (targetCoords.x - sourceCoords.x) / Math.abs(targetCoords.x - sourceCoords.x)
                } else {
                    step.x = (targetCoords.x - sourceCoords.x) / Math.abs(targetCoords.x - sourceCoords.x)
                    step.y = (targetCoords.y - sourceCoords.y) / Math.abs(targetCoords.y - sourceCoords.y)
                }
                const position = { x: sourceCoords.x + step.x, y: sourceCoords.y + step.y }
                removeAllHighlightExceptFirstElement()

                while (position.x !== targetCoords.x || position.y !== targetCoords.y) {
                    // console.log(sourceCoords, targetCoords, position, step)
                    const ndx = position.y * CONTAINER_WIDTH + position.x
                    const area = containerPuzzle.children[ndx]
                    affectedElements.push(area)
                    position.x += step.x
                    position.y += step.y
                }
                affectedElements.push(targetArea)

                for (const element of affectedElements) {
                    addHighlight(element)
                    selectSequence.push(element)
                }
            }
        } else {
            removeAllHighlightExceptFirstElement()
        }
    }
}

const getSelectedWord = (sequence) => {
    const text = sequence.map((e) => e.children[0].innerHTML).join("")
    return text
}

const getClickReleaseWithCallback = (callback) => {
    const clickRelease = () => {
        if (finished) {
            return
        }
        if (selectSequence.length) {
            callback()

            sourceCoords.x = -1
            sourceCoords.y = -1
            selectSequence.splice(0, selectSequence.length)
        }
    }
    return clickRelease
}

const release_callback = () => {
    const selectedText = getSelectedWord(selectSequence)

    const wordlist = Array.from(containerWordlist.children).map((e) => e.innerHTML)
    const wordIndex = wordlist.indexOf(selectedText)
    if (wordIndex > -1) {
        const element = containerWordlist.children[wordIndex]
        element.classList.add(WORD_FOUND_CLASS)
        element.innerHTML += " "
        const color = wordColors.pop()
        element.style.color = color

        const className = `class-${selectedText}`
        const newStyle = `.puzzle-container>.${className} { background-color: ${color}AF; } `
        documentStyleCustom.innerHTML += newStyle

        for (const item of selectSequence) {
            item.classList.add(className)
        }
    }
    for (const item of selectSequence) {
        removeHighlight(item)
    }
    const remainingWords = Array.from(containerWordlist.children).filter((e) => !Array.from(e.classList).includes(WORD_FOUND_CLASS))
    if (remainingWords.length === 0) {
        containerFooter.innerHTML = `Game Finished. <a href="/">Return To Index</a>`
        finished = true
    }
}

const init = () => {
    for (const child of containerPuzzle.children) {
        const span = child.children[0]
        span.addEventListener('mousedown', clickHighlight)
        span.addEventListener('mouseenter', clickDragOver)
    }
    containerPuzzle.addEventListener('mouseup', getClickReleaseWithCallback(release_callback))
    for (const e of containerWordlist.children) {
        wordColors.push(getColorCode())
    }
}

window.onload = init;
