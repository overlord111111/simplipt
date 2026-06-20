const vscode = require('vscode');

function activate(context) {
    console.log('SimpliPT extension ativada');

    const diagnosticCollection = vscode.languages.createDiagnosticCollection('simplipt');
    context.subscriptions.push(diagnosticCollection);

    const lspCommand = vscode.commands.registerCommand('simplipt.startLsp', () => {
        const terminal = vscode.window.createTerminal('SimpliPT LSP');
        terminal.sendText('simplipt lsp');
        terminal.show();
        vscode.window.showInformationMessage('SimpliPT LSP iniciado no terminal');
    });
    context.subscriptions.push(lspCommand);

    const runCommand = vscode.commands.registerCommand('simplipt.run', () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'simplipt') {
            vscode.window.showErrorMessage('Abra um arquivo .spt primeiro');
            return;
        }
        const filePath = editor.document.uri.fsPath;
        const terminal = vscode.window.createTerminal('SimpliPT Run');
        terminal.sendText(`simplipt "${filePath}"`);
        terminal.show();
    });
    context.subscriptions.push(runCommand);

    const dashboardCommand = vscode.commands.registerCommand('simplipt.dashboard', () => {
        const terminal = vscode.window.createTerminal('SimpliPT Dashboard');
        const folder = vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath || '';
        terminal.sendText(folder ? `simplipt dashboard "${folder}"` : 'simplipt dashboard');
        terminal.show();
    });
    context.subscriptions.push(dashboardCommand);

    context.subscriptions.push(
        vscode.commands.registerCommand('simplipt.format', () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor || editor.document.languageId !== 'simplipt') return;
            const filePath = editor.document.uri.fsPath;
            const terminal = vscode.window.createTerminal('SimpliPT Format');
            terminal.sendText(`simplipt formatar "${filePath}"`);
            terminal.show();
        })
    );

    const hoverProvider = vscode.languages.registerHoverProvider('simplipt', {
        provideHover(document, position) {
            const word = document.getText(document.getWordRangeAtPosition(position));
            const palavras = {
                'se': 'Inicia um bloco condicional',
                'senao': 'Alternativa para o se',
                'fim': 'Fecha um bloco',
                'para': 'Loop sobre colecao ou intervalo',
                'enquanto': 'Loop enquanto condicao for verdadeira',
                'funcao': 'Declara uma funcao',
                'fn': 'Declara uma funcao (anonima)',
                'retornar': 'Retorna um valor de uma funcao',
                'falar': 'Exibe uma mensagem no console',
                'tentar': 'Inicia um bloco de tratamento de erro',
                'capturar': 'Captura excecao do bloco tentar',
                'usar': 'Importa um modulo',
                'classe': 'Define uma classe',
                'novo': 'Cria uma instancia de classe',
                'este': 'Referencia a instancia atual (self)',
                'super': 'Referencia a classe base',
                'nada': 'Valor nulo (None)',
                'verdadeiro': 'Valor booleano verdadeiro',
                'falso': 'Valor booleano falso',
                'eh': 'Operador de igualdade',
                'e': 'Operador logico E',
                'ou': 'Operador logico OU',
                'nao': 'Operador de negacao',
            };
            if (palavras[word]) {
                return new vscode.Hover(`**${word}** - ${palavras[word]}`);
            }
        }
    });
    context.subscriptions.push(hoverProvider);
}

function deactivate() {}

module.exports = { activate, deactivate };
