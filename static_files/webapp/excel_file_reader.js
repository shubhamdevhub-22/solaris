class TableXLSX {
    /**
     * @param {HTMLTableElement} root The table element which will display the XLSX data.
     */
    constructor(root) {
        this.root = root;
    }

    /**
* Clears existing data in the table and replaces it with new data.
*
* @param {string[][]} data A 2D array of data to be used as the table body
* @param {string[]} headerColumns List of headings to be used
*/
    update(data, headerColumns = []) {
        this.clear();
        this.setHeader(headerColumns);
        this.setBody(data);
    }

    /**
     * Clears all contents of the table (incl. the header).
     */
    clear() {
        this.root.innerHTML = "";
    }

    /**
     * Sets the table header.
     *
     * @param {string[]} headerColumns List of headings to be used
     */
    setHeader(headerColumns) {
        this.root.insertAdjacentHTML(
            "afterbegin",
            `
              <thead>
                  <tr>
                      ${headerColumns.map((text) => `<th>${text}</th>`).join("")}
                  </tr>
              </thead>
          `
        );
    }

    /**
     * Sets the table body.
     *
     * @param {string[][]} data A 2D array of data to be used as the table body
     */

    setBody(data) {
        const rowsHtml = data.map((row, index) => {
            console.log(index)
            if (index <= 11) {
                return `
                      <tr>
                          ${row.map((text) => `<td>${text}</td>`).join("")}
                      </tr>
                  `;
            }
        });

        this.root.insertAdjacentHTML(
            "beforeend",
            `
              <tbody>
                  ${rowsHtml.join("")}
              </tbody>
          `
        );
    }
}

const xlsxFileInput = file_root
const tableContainer = document.querySelector("#tableContainer");
const excelTable = new TableXLSX(table_root);

xlsxFileInput.addEventListener("change", (e) => {
    const file = xlsxFileInput.files[0];
    if (file) {
        const reader = new FileReader();

        reader.onload = function (e) {
            const data = new Uint8Array(e.target.result);
            const workbook = XLSX.read(data, { type: "array" });
            const sheetName = workbook.SheetNames[0];
            const sheet = workbook.Sheets[sheetName];
            const excelData = XLSX.utils.sheet_to_json(sheet, { header: 1 ,blankRows: true,defval: '',});

            excelTable.update(excelData.slice(1), excelData[0]);
            tableContainer.style.display = "block";
        };

        reader.readAsArrayBuffer(file);
    }
});