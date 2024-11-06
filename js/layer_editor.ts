import type { AnyModel, RenderProps } from "@anywidget/types";
import { css, html, LitElement, PropertyValues, TemplateResult } from "lit";
import { property, query } from "lit/decorators.js";

import { legacyStyles } from "./ipywidgets_styles";
import { materialStyles, flexStyles } from "./styles";
import {
    reverseMap,
    updateChildren,
    SelectOption,
    renderSelect,
} from "./utils";
import { PaletteEditor } from "./palette_editor";

import "./container";

export interface LayerEditorModel {
    title: string;
    type: string;
    band_names: Array<string>;
    colormaps: Array<string>;
    children: any;
}

class RasterLayerEditor extends LitElement {
    static get componentName() {
        return `raster-layer-editor-widget`;
    }

    static styles = [
        flexStyles,
        legacyStyles,
        materialStyles,
        css`
            fieldset {
                border: none;
                margin: 0;
                padding: 0;
            }

            label {
                vertical-align: middle;
            }

            input[type="radio"] {
                margin: 0;
                vertical-align: middle;
            }

            .hidden {
                display: none;
            }
        `,
    ];

    @property() colorModel: string = "";
    @property() bandNames: Array<string> = [];
    @property() selectedBands: Array<string> = [];
    @property() stretchOptions: Array<SelectOption> = [
        { label: "Custom", value: "custom" },
        { label: "1σ", value: "sigma-1" },
        { label: "2σ", value: "sigma-2" },
        { label: "3σ", value: "sigma-3" },
        { label: "90%", value: "percent-90" },
        { label: "98%", value: "percent-98" },
        { label: "100%", value: "percent-100" },
    ];
    @property() stretch: string = this.stretchOptions[0].value;
    @property() minValue: number | undefined = undefined;
    @property() maxValue: number | undefined = undefined;
    @property() minAndMaxValuesLocked: boolean = false;
    @property() opacity: number | undefined = undefined;
    @property() colorRamp: string = "";
    @property() gamma: number | undefined = undefined;
    @property() colormaps: Array<string> = [];

    render() {
        return html`
            <div class="vertical-flex">
                <div class="horizontal-flex">
                    ${this.renderColorModelRadio("1 band (Grayscale)", "gray")}
                    ${this.renderColorModelRadio("3 bands (RGB)", "rgb")}
                </div>
                <div id="band-selection" class="horizontal-flex">
                    ${this.selectedBands.map((band) => {
                        return this.renderBandSelection(band);
                    })}
                </div>
                <div class="horizontal-flex">
                    <span class="legacy-text">Stretch:</span>
                    ${renderSelect(
                        this.stretchOptions,
                        this.stretch,
                        this.onStretchChanged
                    )}
                    <button
                        class="legacy-button"
                        @click="${this.onRefreshButtonClicked}"
                    >
                        <span class="material-symbols-outlined">&#xe627;</span>
                    </button>
                </div>
                <div class="horizontal-flex">
                    <span class="legacy-text">Range:</span>
                    <input
                        type="text"
                        id="min"
                        name="min"
                        .value="${this.minValue}"
                        @change="${this.onMinTextChanged}"
                        ?disabled="${this.minAndMaxValuesLocked}"
                    />
                    <span class="legacy-text">to</span>
                    <input
                        type="text"
                        id="max"
                        name="max"
                        .value="${this.maxValue}"
                        @change="${this.onMaxTextChanged}"
                        ?disabled="${this.minAndMaxValuesLocked}"
                    />
                </div>
                <div class="horizontal-flex">
                    <span class="legacy-text">Opacity:</span>
                    <input
                        type="range"
                        id="opacity"
                        name="opacity"
                        min="0"
                        max="1.0"
                        step="0.01"
                        .value=${this.opacity}
                        @input=${this.onOpacityChanged}
                        @change=${this.onOpacityChanged}
                    />
                    <span class="legacy-text">${this.opacity}</span>
                </div>
                <div
                    class="horizontal-flex ${this.showIf(
                        this.colorModel === "gray"
                    )}"
                >
                    ${this.renderColorRampRadio("Palette", "palette")}
                    ${this.renderColorRampRadio("Gamma", "gamma")}
                </div>
                <palette-editor
                    class="${this.showIf(this.showPaletteEditor())}"
                    .colormaps="${this.colormaps}"
                >
                    <slot></slot>
                </palette-editor>
                <div
                    class="horizontal-flex ${this.showIf(
                        this.showGammaSlider()
                    )}"
                >
                    <span class="legacy-text">Gamma:</span>
                    <input
                        type="range"
                        id="gamma"
                        name="gamma"
                        min="0.1"
                        max="10"
                        step="0.01"
                        .value=${this.gamma}
                        @input=${this.onGammaChanged}
                        @change=${this.onGammaChanged}
                    />
                    <span class="legacy-text">${this.gamma}</span>
                </div>
            </div>
        `;
    }

    private showIf(value: boolean): string {
        return value ? "" : "hidden";
    }

    private showGammaSlider(): boolean {
        return this.colorRamp === "gamma" || this.colorModel === "rgb";
    }

    private showPaletteEditor(): boolean {
        return this.colorRamp === "palette" && this.colorModel === "gray";
    }

    private renderColorModelRadio(
        label: string,
        value: string
    ): TemplateResult {
        return html`
            <span>
                <input
                    type="radio"
                    id="${value}"
                    name="color-model"
                    value="${value}"
                    @click="${this.onColorModelChanged}"
                    ?checked=${this.colorModel === value}
                />
                <label class="legacy-text">${label}</label>
            </span>
        `;
    }

    private renderColorRampRadio(label: string, value: string): TemplateResult {
        return html`
            <span>
                <input
                    type="radio"
                    id="${value}"
                    name="color-ramp"
                    value="${value}"
                    @click="${this.onColorRampChanged}"
                    ?checked=${this.colorRamp === value}
                />
                <label class="legacy-text">${label}</label>
            </span>
        `;
    }

    private onColorRampChanged(event: Event): void {
        const target = event.target as HTMLInputElement;
        this.colorRamp = target.value;
    }

    private renderBandSelection(value: string): TemplateResult {
        const options = this.bandNames.map(
            (name) => ({ label: name, value: name } as SelectOption)
        );
        return renderSelect(options, value, this.onBandSelectionChanged);
    }

    private onRefreshButtonClicked(event: Event): void {
        event.stopImmediatePropagation();
    }

    private onOpacityChanged(event: Event): void {
        const target = event.target as HTMLInputElement;
        this.opacity = target.valueAsNumber;
    }

    private onGammaChanged(event: Event): void {
        const target = event.target as HTMLInputElement;
        this.gamma = target.valueAsNumber;
    }

    private onMinTextChanged(event: Event): void {
        const target = event.target as HTMLInputElement;
        this.minValue = target.valueAsNumber;
    }

    private onMaxTextChanged(event: Event): void {
        const target = event.target as HTMLInputElement;
        this.maxValue = target.valueAsNumber;
    }

    private onStretchChanged(event: Event): void {
        this.stretch = (event.target as HTMLInputElement).value;
        if (this.stretch === "custom") {
            this.minAndMaxValuesLocked = false;
        } else {
            this.minAndMaxValuesLocked = true;
            this.minValue = undefined;
            this.maxValue = undefined;
        }
        this.dispatchEvent(
            new CustomEvent("calculate-band-stats", {
                bubbles: true,
                composed: true,
            })
        );
    }

    private onBandSelectionChanged(_event: Event): void {
        this.selectedBands = this.getSelectedBands();
    }

    private onColorModelChanged(event: Event): void {
        const target = event.target as HTMLInputElement;
        this.colorModel = target.value;
        if (this.colorModel === "gray") {
            this.selectedBands = Array.from([this.bandNames[0]]);
        } else if (this.colorModel == "rgb") {
            this.selectedBands = Array.from([
                this.bandNames[0],
                this.bandNames[0],
                this.bandNames[0],
            ]);
        }
    }

    private getSelectedBands(): Array<string> {
        const container = this.renderRoot?.querySelector(
            `#band-selection`
        ) as HTMLDivElement;
        return Array.from(container.querySelectorAll("select")).map(
            (input) => (input as unknown as HTMLInputElement).value
        );
    }
}

class VectorLayerEditor extends LitElement {
    static get componentName() {
        return `vector-layer-editor-widget`;
    }

    static styles = [legacyStyles, css``];

    render() {
        return html` <span>VectorLayerEditor</span> `;
    }
}

export class LayerEditor extends LitElement {
    static get componentName() {
        return `layer-editor-widget`;
    }

    static styles = [
        legacyStyles,
        css`
            .hidden {
                display: none;
            }

            .confirm-button {
                padding: 0 20px;
            }

            .confirm-button-row {
                display: flex;
                gap: 4px;
                margin-top: 4px;
            }

            .editor-container {
                max-width: 350px;
            }
        `,
    ];

    private _model: AnyModel<LayerEditorModel> | undefined = undefined;
    private static modelNameToViewName = new Map<
        keyof LayerEditorModel,
        keyof LayerEditor
    >([
        ["title", "title"],
        ["type", "type"],
        ["band_names", "bandNames"],
        ["colormaps", "colormaps"],
        ["children", null],
    ]);
    private static viewNameToModelName = reverseMap(this.modelNameToViewName);

    set model(model: AnyModel<LayerEditorModel>) {
        this._model = model;
        for (const [modelKey, widgetKey] of LayerEditor.modelNameToViewName) {
            if (widgetKey) {
                // Get initial values from the Python model.
                (this as any)[widgetKey] = model.get(modelKey);
                // Listen for updates to the model.
                model.on(`change:${modelKey}`, () => {
                    (this as any)[widgetKey] = model.get(modelKey);
                });
            }
        }
        this.registerCustomMessageHandlers();
    }

    private registerCustomMessageHandlers(): void {
        this._model?.on("msg:custom", (msg: any) => {
            console.log("On msg:custom");
            console.log(msg);
            if ("bandstats" in msg) {
                this.handleBandstatsResponse(msg);
            } else if ("palette" in msg) {
                this.handlePaletteResponse(msg);
            }
        });
    }

    @query("#raster-layer-editor") rasterEditor?: RasterLayerEditor;

    @property() title: string = "";
    @property() type: string = "";
    @property() bandNames: Array<string> = [];
    @property() colormaps: Array<string> = [];

    render() {
        return html`
            <widget-container
                .title="${this.title}"
                @close-clicked="${this.onCloseButtonClicked}"
            >
                <div class="editor-container">
                    <vector-layer-editor-widget
                        class="${this.type == "vector" ? "" : "hidden"}"
                    >
                    </vector-layer-editor-widget>
                    <raster-layer-editor-widget
                        id="raster-layer-editor"
                        class="${this.type == "raster" ? "" : "hidden"}"
                        .bandNames="${this.bandNames}"
                        .colormaps="${this.colormaps}"
                        @calculate-band-stats="${this.calculateBandStats}"
                        @on-palette-changed="${this.onPaletteChanged}"
                    >
                        <slot></slot>
                    </raster-layer-editor-widget>
                    <div class="${this.type == "" ? "" : "hidden"}">
                        <span>Vis params are uneditable</span>
                    </div>
                </div>
                <div class="confirm-button-row">
                    <button class="legacy-button primary confirm-button">
                        Import
                    </button>
                    <button class="legacy-button confirm-button">Apply</button>
                </div>
            </widget-container>
        `;
    }

    private onCloseButtonClicked(_: Event) {
        this._model?.send({ type: "click", id: "close" });
    }

    private calculateBandStats(event: Event) {
        console.log(`calculateBandStats:`);
        console.log(event);

        this._model?.send({
            type: "calculate",
            id: "band-stats",
            detail: {
                bands: this.rasterEditor?.selectedBands,
                stretch: this.rasterEditor?.stretch,
            },
        });
    }

    private onPaletteChanged(event: Event) {
        console.log(`onPaletteChanged:`);
        console.log(event);

        this._model?.send({
            type: "calculate",
            id: "palette",
            detail: {
                colormap: event.detail.colormap,
                classes: event.detail.classes,
                palette: event.detail.palette,
                bandMin: this.rasterEditor?.minValue,
                bandMax: this.rasterEditor?.maxValue,
            },
        });
    }

    private handleBandstatsResponse(response: any): void {
        if (this.rasterEditor) {
            if (response.bandstats.stretch === this.rasterEditor.stretch) {
                this.rasterEditor.minValue = response.bandstats.min;
                this.rasterEditor.maxValue = response.bandstats.max;
            }
        }
    }

    private handlePaletteResponse(response: any): void {
        const paletteEditor = this.rasterEditor?.renderRoot?.querySelector(
            "palette-editor"
        ) as PaletteEditor;
        if (response.palette.palette) {
            paletteEditor.palette = response.palette.palette;
        }
    }

    updated(changedProperties: PropertyValues<LayerEditor>) {
        // Update the model properties so they're reflected in Python.
        for (const [viewProp, _] of changedProperties) {
            const castViewProp = viewProp as keyof LayerEditor;
            if (LayerEditor.viewNameToModelName.has(castViewProp)) {
                const modelProp =
                    LayerEditor.viewNameToModelName.get(castViewProp);
                this._model?.set(modelProp as any, this[castViewProp] as any);
            }
        }
        this._model?.save_changes();
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(RasterLayerEditor.componentName)) {
    customElements.define(RasterLayerEditor.componentName, RasterLayerEditor);
}
if (!customElements.get(VectorLayerEditor.componentName)) {
    customElements.define(VectorLayerEditor.componentName, VectorLayerEditor);
}
if (!customElements.get(LayerEditor.componentName)) {
    customElements.define(LayerEditor.componentName, LayerEditor);
}

async function render({ model, el }: RenderProps<LayerEditorModel>) {
    const widget = document.createElement(
        LayerEditor.componentName
    ) as LayerEditor;
    widget.model = model;
    el.appendChild(widget);

    updateChildren(widget, model);
    model.on("change:children", () => {
        updateChildren(widget, model);
    });
}

export default { render };
